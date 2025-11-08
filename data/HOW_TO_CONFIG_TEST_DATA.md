# Test Data Configuration Guide

This guide explains how to configure Excel files for generating test cases using the Combination Engine.

## Table of Contents
- [Overview](#overview)
- [Cross-Life Configuration](#cross-life-configuration)
- [Single-Life Configuration](#single-life-configuration)
- [Key Differences](#key-differences)
- [Common Pitfalls](#common-pitfalls)
- [Examples](#examples)

---

## Overview

The combination engine supports two main scenarios:

| Scenario | Description | Use Case |
|----------|-------------|----------|
| **Cross-Life** | Multiple different people in one policy | Family insurance (spouse, children) |
| **Single-Life** | One person with multiple roles/coverages | Individual with both ML and O coverage |

Both scenarios use the `/api/v1/combination-test-case` endpoint which:
1. Reads your Excel file with possible test data
2. Generates all combinations (Cartesian product)
3. **Expands arrays**: Converts `[]` notation to indexed `[0]`, `[1]`, etc.

---

## Cross-Life Configuration

### 📋 Definition
- **isCrossLife = TRUE**
- Multiple **different people** with unique IDs
- Each person can have different ages, attributes

### 🔧 Configuration Pattern

Use **indexed array notation `[0]`, `[1]`** for each person:

```
[Request][Body]data.filters.isCrossLife[Type:bool]
  Row 1: TRUE

[Request][Body]data.clientProfiles[0].id
  Row 1: 7e3fe367-4acc-4bc1-a522-461ab94ecfc9

[Request][Body]data.clientProfiles[0].clientType
  Row 1: ML

[Request][Body]data.clientProfiles[0].personalInfo.age[Type:int]
  Row 1: 16
  Row 2: 17
  Row 3: 50
  Row 4: 99

[Request][Body]data.clientProfiles[0].personalInfo.isSmoker[Type:bool]
  Row 1: true
  Row 2: false

[Request][Body]data.clientProfiles[1].id
  Row 1: 12345678-1234-1234-1234-123456789012

[Request][Body]data.clientProfiles[1].clientType
  Row 1: O

[Request][Body]data.clientProfiles[1].personalInfo.age[Type:int]
  Row 1: 18
  Row 2: 47
  Row 3: 90

[Request][Body]data.clientProfiles[1].relationship
  Row 1: SP
  Row 2: CH
```

### ✅ Result

**Cartesian Product:**
- Person [0]: 4 ages × 2 smoker = 8 combinations
- Person [1]: 3 ages × 2 relationships = 6 combinations
- **Total: 8 × 6 = 48 test cases**

Each test case has:
- Person 0 (ML) with one age variation
- Person 1 (O) with a different person ID and their own age variation

### 📝 Example Output

```json
{
  "clientProfiles": [
    {
      "id": "7e3fe367-4acc-4bc1-a522-461ab94ecfc9",
      "clientType": "ML",
      "personalInfo": { "age": 16, "isSmoker": true }
    },
    {
      "id": "12345678-1234-1234-1234-123456789012",
      "clientType": "O",
      "personalInfo": { "age": 18 },
      "relationship": "SP"
    }
  ]
}
```

---

## Single-Life Configuration

### 📋 Definition
- **isCrossLife = FALSE**
- One person with **same ID** in multiple roles
- All attributes (age, DOB, etc.) must be **identical** across profiles

### 🔧 Configuration Pattern

Use **dynamic array notation `[]`** with **duplicated values**:

```
[Request][Body]data.filters.isCrossLife[Type:bool]
  Row 1: FALSE

[Request][Body]data.clientProfiles[].id
  Row 1: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee,aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  (Same ID twice - same person!)

[Request][Body]data.clientProfiles[].clientType
  Row 1: ML,O
  (Two roles for the same person)

[Request][Body]data.clientProfiles[].personalInfo.age[Type:int]
  Row 1: 25,25
  Row 2: 30,30
  Row 3: 45,45
  (MUST duplicate the age - same person = same age!)

[Request][Body]data.clientProfiles[].personalInfo.isSmoker[Type:bool]
  Row 1: true,true
  Row 2: false,false

[Request][Body]data.clientProfiles[].personalInfo.dob
  Row 1: 02.09.1998,02.09.1998
  (Same DOB - same person!)

[Request][Body]data.clientProfiles[].relationship
  Row 1: OS,OS
```

### ✅ Result

**Cartesian Product:**
- 3 age options (25, 30, 45)
- 2 smoker options (true, false)
- **Total: 3 × 2 = 6 test cases**

### 🔄 Array Expansion

The combination service automatically expands `[]` to `[0]`, `[1]`:

**Input:**
```
clientProfiles[].age = "25,25"
```

**Output after expansion:**
```
clientProfiles[0].age = 25
clientProfiles[1].age = 25
```

### 📝 Example Output

```json
{
  "clientProfiles": [
    {
      "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "clientType": "ML",
      "personalInfo": { "age": 25, "isSmoker": true },
      "relationship": "OS"
    },
    {
      "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "clientType": "O",
      "personalInfo": { "age": 25, "isSmoker": true },
      "relationship": "OS"
    }
  ]
}
```

---

## Key Differences

| Aspect | Cross-Life | Single-Life |
|--------|------------|-------------|
| **isCrossLife** | `TRUE` | `FALSE` |
| **Array Notation** | Indexed: `[0]`, `[1]` | Dynamic: `[]` |
| **Person IDs** | Different UUIDs | Same UUID (duplicated) |
| **Age Configuration** | Can be different:<br>`[0].age: 16,17,50`<br>`[1].age: 18,47,90` | Must be same:<br>`[].age: 25,25`<br>`[].age: 30,30` |
| **Value Pattern** | Single values per row | Comma-separated duplicates |
| **Example** | `uuid-person1` vs `uuid-person2` | `uuid-same,uuid-same` |
| **DOB** | Can differ | Must match |
| **All Fields** | Independent per person | **MUST duplicate** |

---

## Common Pitfalls

### ❌ WRONG: Single-Life with Different Ages

```excel
[].age: 25,30
```

This means the **same person has two different ages** - impossible!

### ✅ CORRECT: Single-Life with Same Age

```excel
[].age: 25,25  (Row 1)
[].age: 30,30  (Row 2)
```

This creates **two test cases**, each with the same person at a consistent age.

---

### ❌ WRONG: Single-Life Using Indexed Arrays

```excel
[0].age: 25
[1].age: 30
```

This creates a Cartesian product: `[0]=25` with `[1]=30` (same person, different ages).

### ✅ CORRECT: Single-Life Using Dynamic Arrays

```excel
[].age: 25,25
[].age: 30,30
```

---

### ❌ WRONG: Cross-Life with Dynamic Arrays

```excel
[].id: uuid1,uuid2
[].age: 16,18
```

This is ambiguous - use indexed arrays for clarity.

### ✅ CORRECT: Cross-Life with Indexed Arrays

```excel
[0].id: uuid1
[0].age: 16,17,50
[1].id: uuid2
[1].age: 18,47,90
```

---

## Examples

### Example 1: Cross-Life - Family Policy

**Goal:** Test husband (ML, ages 16-99) and wife (O, ages 18-90)

**Configuration:**
- `[0].id`: `husband-uuid`
- `[0].clientType`: `ML`
- `[0].age`: `16`, `17`, `50`, `99` (4 rows)
- `[1].id`: `wife-uuid`
- `[1].clientType`: `O`
- `[1].age`: `18`, `47`, `90` (3 rows)

**Result:** 4 × 3 = 12 test cases with all age combinations

---

### Example 2: Single-Life - Individual with Dual Coverage

**Goal:** Test one person with both ML and O roles at ages 25, 30, 45

**Configuration:**
- `[].id`: `person-uuid,person-uuid`
- `[].clientType`: `ML,O`
- `[].age`:
  - Row 1: `25,25`
  - Row 2: `30,30`
  - Row 3: `45,45`

**Result:** 3 test cases, each with the same person at one age

---

### Example 3: Combined Variations

**Goal:** Single-life with age and smoker variations

**Configuration:**
- `[].age`:
  - Row 1: `25,25`
  - Row 2: `30,30`
  - Row 3: `45,45`
- `[].isSmoker`:
  - Row 1: `true,true`
  - Row 2: `false,false`

**Result:** 3 ages × 2 smoker = 6 test cases

---

## Null Values

Use `[NULL]` sentinel for null values in JSON:

```excel
[Request][Body]data.clientProfiles[].personalInfo.nationality.value
  Row 1: [NULL],[NULL]

[Request][Body]data.clientProfiles[].personalInfo.countryOfBirth.code
  Row 1: [NULL],[NULL]
```

This converts to `null` in the JSON output.

Other sentinels:
- `[EMPTY]` or `[EMPTY_STRING]` → `""`
- `[EMPTY_ARRAY]` → `[]`
- `[EMPTY_OBJECT]` → `{}`

---

## Files in This Directory

- `cross-life-example.xlsx` - Example with 2 different people (48 combinations)
- `single-life-example.xlsx` - Example with 1 person in 2 roles (6 combinations)
- `vpms_get_product_list_request.json` - Reference JSON structure

---

## Quick Reference

### Single-Life Template
```
isCrossLife: FALSE
[].id: same-uuid,same-uuid
[].clientType: ML,O
[].age: 25,25 | 30,30 | 45,45
[].dob: same-date,same-date
[].isSmoker: true,true | false,false
```

### Cross-Life Template
```
isCrossLife: TRUE
[0].id: uuid-person-1
[0].clientType: ML
[0].age: 16 | 17 | 50 | 99
[1].id: uuid-person-2
[1].clientType: O
[1].age: 18 | 47 | 90
```

---

## Need Help?

1. Check example files in this directory
2. Review the API documentation at `/docs`
3. Test with small datasets first
4. Verify output has correct number of combinations

**Formula:** Total = Product of all parameter value counts
- Cross-life: 4 ages × 2 smoker × 3 ages × 2 relationships = 48
- Single-life: 3 ages × 2 smoker = 6
