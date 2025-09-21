# Position Sorting Options

## Huidige Implementatie (NIEUWE)
- **Ascending**: Positie 0 bovenaan (#1, #2, #3, ..., UNRANKED)
- **Descending**: Positie 0 onderaan (UNRANKED, ..., #3, #2, #1)

## Alternatief 1: Altijd positie 0 bovenaan
```javascript
case 'position':
  // Unranked players always at top regardless of sort direction
  aVal = a.position === 0 ? -999999 : a.position;
  bVal = b.position === 0 ? -999999 : b.position;
  break;
```

## Alternatief 2: Altijd positie 0 onderaan (ORIGINEEL)
```javascript
case 'position':
  // Unranked players always at bottom regardless of sort direction  
  aVal = a.position === 0 ? 999999 : a.position;
  bVal = b.position === 0 ? 999999 : b.position;
  break;
```

## Alternatief 3: Slimme sortering
```javascript
case 'position':
  // Smart sorting: ranked players by position, unranked grouped separately
  if (a.position === 0 && b.position === 0) {
    // Both unranked, sort by name
    aVal = a.uname || '';
    bVal = b.uname || '';
  } else if (a.position === 0) {
    // a is unranked, put at desired location
    aVal = sortDirection === 'asc' ? -1 : 999999;
    bVal = b.position;
  } else if (b.position === 0) {
    // b is unranked
    aVal = a.position;
    bVal = sortDirection === 'asc' ? -1 : 999999;
  } else {
    // Both ranked, normal sorting
    aVal = a.position;
    bVal = b.position;
  }
  break;
```