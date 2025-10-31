from pathlib import Path
import subprocess, datetime, re, asyncio, os, sys
from typing import Tuple, List, Dict, Any, AsyncGenerator
import xml.etree.ElementTree as ET
import time
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

def run_robot_and_get_report(gen_dir: Path, report_dir: Path) -> Tuple[Path, List[str], str]:
    """
    Run Robot Framework tests and generate timestamped report.
    
    Returns:
        Tuple of (output_directory, logs, timestamp)
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = report_dir / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    # Run Robot Framework on generated dir
    cmd = ["robot", "--outputdir", str(out_dir), str(gen_dir)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logs = []
    if proc.stdout:
        for line in proc.stdout:
            logs.append(line.rstrip())
    proc.wait()
    return out_dir, logs, ts


def _read_process_output(proc: subprocess.Popen, output_queue: queue.Queue):
    """
    Read subprocess output in a separate thread and put lines in a queue.
    This function runs in a background thread.
    """
    if proc.stdout:
        for line in iter(proc.stdout.readline, b''):
            output_queue.put(('line', line))
    proc.stdout.close()
    proc.wait()
    output_queue.put(('done', proc.returncode))


async def run_robot_streaming(gen_dir: Path, report_dir: Path) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run Robot Framework tests with real-time streaming of test case results.
    Cross-platform implementation using threading (works on Windows and Linux).

    Yields:
        Dict with keys:
            - 'type': 'connect' | 'process' | 'pass' | 'fail' | 'skip' | 'done'
            - 'data': {'case': str, 'status': str, 'message': str (optional)}
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = report_dir / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    # Send connection event
    yield {
        'type': 'connect',
        'data': {'status': 'connected', 'message': 'Test execution started'}
    }

    # Run Robot Framework with --console verbose for real-time output
    # Use subprocess.Popen with threading for cross-platform compatibility
    cmd = ["robot", "--console", "verbose", "--outputdir", str(out_dir), str(gen_dir)]
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}

    # Start subprocess
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        bufsize=1  # Line buffered
    )

    # Create queue for communication between threads
    output_queue: queue.Queue = queue.Queue()

    # Start reader thread
    reader_thread = threading.Thread(
        target=_read_process_output,
        args=(proc, output_queue),
        daemon=True
    )
    reader_thread.start()
    
    # Regex patterns for Robot Framework --console verbose output:
    # 1. Test header line: "TC 001" or "Generated.TC 001"
    # 2. Test result: "Generated.TC 077 | PASS |" or "Generated.TC 077 | FAIL | Error message"
    # 3. Skip detection: "SKIP" keyword in result line
    test_header_pattern = re.compile(r"^(?:Generated\.)?(\w+[_\s]\d+)\s*$")
    test_result_pattern = re.compile(r"^(?:Generated\.)?(\w+[_\s]\d+)\s+\|\s+(PASS|FAIL|SKIP)\s+\|(.*)$")

    output_xml_path = out_dir / "output.xml"

    # Read output from queue
    process_running = True
    while process_running:
        try:
            # Get item from queue with timeout
            item = await asyncio.get_event_loop().run_in_executor(
                None,
                output_queue.get,
                True,  # block
                0.1    # timeout
            )

            msg_type, data = item

            if msg_type == 'done':
                # Process finished
                process_running = False
                break
            elif msg_type == 'line':
                line = data.decode('utf-8').rstrip()

                # Check for test result first (has priority)
                result_match = test_result_pattern.match(line)
                if result_match:
                    case_name_raw = result_match.group(1).strip()
                    # Normalize: "TC 089" → "TC_089"
                    case_name = case_name_raw.replace(' ', '_')
                    status = result_match.group(2).upper()  # 'PASS', 'FAIL', or 'SKIP'
                    console_message = result_match.group(3).strip() if len(result_match.groups()) > 2 else ''

                    # Map to event type
                    event_type = status.lower()  # 'pass', 'fail', or 'skip'

                    # Use console message directly during streaming
                    # Note: Don't try to parse output.xml here - it's incomplete while robot is running
                    message = console_message if console_message else f'Test {status.lower()}'

                    yield {
                        'type': event_type,
                        'data': {
                            'case': case_name,
                            'status': status.lower(),
                            'message': message
                        }
                    }
                    continue

                # Check for test start (process state)
                start_match = test_header_pattern.match(line)
                if start_match:
                    case_name_raw = start_match.group(1).strip()
                    # Normalize: "TC 089" → "TC_089"
                    case_name = case_name_raw.replace(' ', '_')

                    yield {
                        'type': 'process',
                        'data': {
                            'case': case_name,
                            'status': 'running',
                            'message': f'Running {case_name}'
                        }
                    }
        except queue.Empty:
            # No data available, continue loop
            # This allows other async tasks to run
            await asyncio.sleep(0.01)
            continue
    
    # Parse output.xml for final summary
    summary = parse_output_xml(out_dir / "output.xml")
    yield {
        'type': 'done',
        'data': {
            'status': 'completed',
            'summary': summary,
            'timestamp': ts,
            'message': f"Completed: {summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped"
        }
    }


def parse_output_xml(xml_path: Path) -> Dict[str, int]:
    """
    Parse Robot Framework output.xml to extract test statistics.
    
    Returns:
        Dict with keys: total, passed, failed, skipped
    """
    if not xml_path.exists():
        return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}

    # Try to parse the XML with a few retries to handle the case where Robot
    # Framework is still writing the file and it's temporarily empty/incomplete.
    try:
        tree = _load_xml_with_retries(xml_path)
        root = tree.getroot()

        # Find <statistics> -> <total> -> <stat>
        stats = root.find('.//statistics/total/stat')
        if stats is not None:
            total = int(stats.get('pass', 0)) + int(stats.get('fail', 0)) + int(stats.get('skip', 0))
            return {
                'total': total,
                'passed': int(stats.get('pass', 0)),
                'failed': int(stats.get('fail', 0)),
                'skipped': int(stats.get('skip', 0))
            }
    except ET.ParseError as e:
        print(f"Error parsing output.xml (parse error) {xml_path}: {e}")
    except Exception as e:
        print(f"Error parsing output.xml: {e}")

    return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}


def get_test_error_details(xml_path: Path, test_name: str) -> str:
    """
    Extract detailed error message from Robot Framework output.xml for a specific test.
    
    Parses the error to show expected vs actual values in a readable format.
    
    Args:
        xml_path: Path to output.xml file
        test_name: Name of the test case (e.g., "TC_001")
    
    Returns:
        Formatted error message with expected vs actual, or empty string if not found
    """
    if not xml_path.exists():
        return ""

    try:
        tree = _load_xml_with_retries(xml_path)
        root = tree.getroot()
        
        # Find the test case by name
        # Robot Framework XML structure: <robot> -> <suite> -> <suite> -> <test name="TC_001">
        for test in root.findall('.//test'):
            test_name_attr = test.get('name', '')
            # Normalize name (handle both "TC 001" and "TC_001")
            normalized_name = test_name_attr.replace(' ', '_')
            
            if normalized_name == test_name or test_name_attr == test_name:
                # Get the test status element
                status = test.find('status')
                if status is not None and status.get('status') == 'FAIL':
                    # Get the error message from the status text
                    error_msg = status.text or ""
                    
                    # Also check for failed keywords with more detailed messages
                    detailed_error = extract_keyword_error(test)
                    if detailed_error:
                        return detailed_error
                    
                    # Parse common error formats
                    if error_msg:
                        return format_error_message(error_msg)
                    
                    return "Test failed"
                
                break
    
    except ET.ParseError as e:
        print(f"Error extracting test details from output.xml (parse error): {e}")
    except Exception as e:
        print(f"Error extracting test details from output.xml: {e}")
    
    return ""


def _load_xml_with_retries(xml_path: Path, retries: int = 20, delay: float = 0.2) -> ET.ElementTree:
    """
    Helper to parse an XML file with retries to handle transient incomplete writes.

    The function checks that the file is non-empty, contains an XML declaration at the
    head and a closing </robot> tag near the tail before attempting to parse. This
    prevents attempting to parse while Robot Framework is still writing the file.

    Raises ET.ParseError if unable to parse after retries.
    """
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            try:
                st = xml_path.stat()
                size = st.st_size
            except FileNotFoundError:
                # File not yet created
                last_exc = ET.ParseError("File not found")
                print(f"[parse retry {attempt}/{retries}] output.xml not found yet")
                time.sleep(delay)
                continue

            if size == 0:
                last_exc = ET.ParseError("Empty file")
                print(f"[parse retry {attempt}/{retries}] output.xml is empty (size=0)")
                time.sleep(delay)
                continue

            # Read a small head and tail to check for XML start and closing tag
            head = b""
            tail = b""
            try:
                with xml_path.open('rb') as fh:
                    head = fh.read(256)
                    # Seek to near the end for tail check
                    if size > 4096:
                        fh.seek(max(0, size - 4096))
                    else:
                        fh.seek(0)
                    tail = fh.read()
            except Exception as e:
                last_exc = e
                print(f"[parse retry {attempt}/{retries}] could not read file head/tail: {e}")
                time.sleep(delay)
                continue

            if b'<?xml' not in head:
                last_exc = ET.ParseError("Missing XML declaration")
                print(f"[parse retry {attempt}/{retries}] output.xml missing XML declaration in head")
                time.sleep(delay)
                continue

            if b'</robot>' not in tail:
                last_exc = ET.ParseError("Missing closing </robot> tag")
                print(f"[parse retry {attempt}/{retries}] output.xml missing closing </robot> in tail (size={size})")
                time.sleep(delay)
                continue

            # Basic sanity checks passed, try parsing
            return ET.parse(xml_path)

        except ET.ParseError as e:
            last_exc = e
            print(f"[parse retry {attempt}/{retries}] ET.ParseError while parsing output.xml: {e}")
            time.sleep(delay)
            continue
        except Exception as e:
            last_exc = e
            print(f"[parse retry {attempt}/{retries}] unexpected error while parsing output.xml: {e}")
            time.sleep(delay)
            continue

    # After retries exhausted, raise last parse error
    if last_exc:
        raise last_exc
    raise ET.ParseError("Unknown XML parse error after retries")


def format_error_message(error_msg: str) -> str:
    """
    Format error message to show expected vs actual values clearly.
    
    Args:
        error_msg: Raw error message from Robot Framework
    
    Returns:
        Formatted error message
    """
    # Pattern 1: "200 != 201" (comparison)
    if "!=" in error_msg:
        parts = error_msg.split("!=")
        if len(parts) == 2:
            actual = parts[0].strip()
            expected = parts[1].strip()
            return f"Expected: {expected}, but got: {actual}"
    
    # Pattern 2: "200 == 201" (should not be equal)
    if "==" in error_msg and "should not" in error_msg.lower():
        parts = error_msg.split("==")
        if len(parts) == 2:
            val1 = parts[0].strip()
            val2 = parts[1].strip()
            return f"Expected different values, but both were: {val1}"
    
    # Pattern 3: Already formatted "Expected: X but was: Y"
    if "expected:" in error_msg.lower() and ("but" in error_msg.lower() or "got:" in error_msg.lower()):
        return error_msg
    
    # Pattern 4: "AssertionError: message"
    if "AssertionError:" in error_msg:
        return error_msg.split("AssertionError:", 1)[1].strip()
    
    # Default: return as is
    return error_msg


def extract_keyword_error(test_element) -> str:
    """
    Extract error details from failed keywords within a test.
    Looks for assertion errors and comparison failures.
    
    Args:
        test_element: XML element for the test case
    
    Returns:
        Formatted error message from failed keyword
    """
    try:
        # Find all keywords in the test
        for kw in test_element.findall('.//kw'):
            status = kw.find('status')
            if status is not None and status.get('status') == 'FAIL':
                kw_name = kw.get('name', 'Keyword')
                kw_msg = status.text or ""
                
                # Special handling for common assertion keywords
                if "Should Be Equal" in kw_name:
                    # Get the arguments to see expected vs actual
                    args = [arg.text for arg in kw.findall('arg') if arg.text]
                    if len(args) >= 2:
                        actual = args[0]
                        expected = args[1]
                        return f"Expected: {expected}, but got: {actual} ({kw_name})"
                
                elif "Should Be Equal As Integers" in kw_name or "Should Be Equal As Numbers" in kw_name:
                    args = [arg.text for arg in kw.findall('arg') if arg.text]
                    if len(args) >= 2:
                        actual = args[0]
                        expected = args[1]
                        return f"Expected: {expected}, but got: {actual}"
                
                elif "Status Should Be" in kw_name:
                    args = [arg.text for arg in kw.findall('arg') if arg.text]
                    if len(args) >= 2:
                        expected = args[0]
                        return f"Expected status: {expected}, but request failed: {kw_msg}"
                
                # Check for FAIL level messages
                msg_elements = kw.findall('.//msg')
                for msg in msg_elements:
                    if msg.get('level') == 'FAIL':
                        msg_text = msg.text or ""
                        if msg_text and msg_text != kw_msg:
                            return f"{kw_name}: {msg_text}"
                
                # Return keyword error if available
                if kw_msg:
                    return f"{kw_name}: {kw_msg}"
        
    except Exception:
        pass
    
    return ""

