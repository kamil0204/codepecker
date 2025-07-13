# METHOD_CALL Relationship Consistency Fix

## Problem
The codebase had inconsistent relationship types between the server API and call stack viewer:
- **Server queries** used `:CALLS` relationships
- **Call stack viewer** used `:INVOKES` relationships (which was changed to `:METHOD_CALL`)
- This caused Neo4j warnings about missing relationship types

## Solution - Option 1: Standardize on `:METHOD_CALL`

Updated all components to use `:METHOD_CALL` relationships consistently across the entire codebase.

## Changes Made

### 1. **server.py** 
- ✅ Updated `get_class_graph()` endpoint query to use `:METHOD_CALL` instead of `:CALLS`
- ✅ Updated `get_full_graph()` endpoint query to use `:METHOD_CALL` instead of `:CALLS`  
- ✅ Updated statistics query to count `:METHOD_CALL` relationships instead of `:CALLS`
- ✅ Enhanced queries to return proper class.method format for method calls

### 2. **neo4j_graph_db.py**
- ✅ Updated `add_method_call()` to create `:METHOD_CALL` relationships with smart target resolution
- ✅ Updated `print_graph()` to query `:METHOD_CALL` relationships instead of `:CALLS`
- ✅ All relationship queries now consistently use `:METHOD_CALL` type

### 3. **Relationship Architecture**
Now uses a single, consistent relationship type:
- **`:METHOD_CALL`** - Used for all method call relationships
  - Inter-class method calls: `(Method)-[:METHOD_CALL]->(Method)` 
  - Simple method calls: `(Method)-[:METHOD_CALL {method_name: "name"}]->(Method)`
  - Enhanced method calls: `(Method)-[:METHOD_CALL {type: "SIMPLE_CALL"}]->(Method)`

## Benefits

1. **✅ No more Neo4j warnings** - All components use the same relationship type
2. **✅ Consistent data model** - Single relationship type across the entire system
3. **✅ Better relationship data** - Server now shows full class.method paths for calls
4. **✅ Improved maintainability** - Single source of truth for relationship structure

## Verification

To verify the fix is working:

1. **Check relationship types in Neo4j Browser:**
   ```cypher
   CALL db.relationshipTypes()
   ```
   Should show `METHOD_CALL` but no `INVOKES` or `CALLS`

2. **Count relationships:**
   ```cypher
   MATCH ()-[r:METHOD_CALL]->() RETURN count(r) as method_call_count
   ```

3. **Test call stack viewer** - Should no longer show warnings about missing `INVOKES` relationships

## Next Steps

- Clear Neo4j database and re-run ingestion to ensure all relationships use the new type
- Or run this cleanup query in Neo4j Browser:
  ```cypher
  // Remove any old relationship types if they exist
  MATCH ()-[r:CALLS]->() DELETE r;
  MATCH ()-[r:INVOKES]->() DELETE r;
  ```

The warning about missing `INVOKES` relationships should now be completely resolved!
