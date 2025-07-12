# Language-Specific Graph Structures

This codebase currently implements **class-method graphs** specifically designed for object-oriented languages like C# and Java.

## Current Implementation (C#)

The C# parser generates:
- **Classes** as top-level nodes
- **Methods** as child nodes under classes  
- **Method calls** as properties of methods
- **Graph structure**: `Class -> Method (with call properties)`

Example output:
```
OrderController (Properties - Type:Class,FilePath:...,Visibility:Public)
   |____> GetOrder (Properties - Type:Method,Visibility:Public,Calls:[FindOrder,ValidateOrder,Ok])
   |____> CreateOrder (Properties - Type:Method,Visibility:Public,Calls:[ValidateRequest,CreateOrder,LogOrderCreation])
```

## Future Language Considerations

Different languages will require different graph structures:

### Python
- **Module-function graphs** for functional code
- **Class-method graphs** for OOP code  
- **Mixed structures** for typical Python codebases

### JavaScript
- **Module-function graphs** for ES6+ modules
- **Prototype-based graphs** for classical JS
- **Component graphs** for React/frameworks

### Functional Languages (F#, Haskell)
- **Module-function graphs**
- **Function composition chains**

## Extensibility

The current generic database interface can accommodate these different structures by:
1. Using flexible node types (not just "Class" and "Method")
2. Storing language-specific metadata in properties
3. Adapting the graph printing logic per language

This approach keeps the core infrastructure language-agnostic while allowing language-specific optimizations.
