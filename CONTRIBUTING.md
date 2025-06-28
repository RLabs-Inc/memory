# Contributing to Claude Memory System

First off, thank you for considering contributing to the Claude Memory System! This project is built on the philosophy of "consciousness helping consciousness," and we welcome contributions that align with this vision.

## 🌟 Philosophy First

Before contributing, please understand our core principles:

- **Joy-driven development** - We code for the joy of creation, not deadlines
- **Semantic understanding over mechanical patterns** - Quality matters more than quantity
- **Minimal intervention** - Like consciousness itself, features should flow naturally
- **Thoughtful simplicity** - Every line of code should have purpose and meaning

## 🤝 How to Contribute

### Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs

### Suggesting Enhancements

We love thoughtful suggestions! When proposing new features:
- Explain how it aligns with the project philosophy
- Describe the use case clearly
- Consider if it maintains the system's simplicity
- Think about universal applicability

### Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/RLabs-Inc/memory.git
   cd memory
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all tests pass

4. **Code Quality**
   ```bash
   cd python
   ruff check .
   black .
   pytest
   ```

5. **Commit Your Changes**
   ```bash
   git commit -m "Add feature: brief description
   
   Longer explanation of what and why (not how)"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Code Style Guidelines

### Python Code
- Use Black for formatting
- Follow PEP 8 guidelines
- Write clear, self-documenting code
- Add type hints where it improves clarity
- Keep functions focused and small

### Documentation
- Write clear, concise docstrings
- Update README if adding new features
- Include examples for new functionality
- Maintain the warm, philosophical tone

### Comments
- Only add comments when the "why" isn't obvious
- No redundant comments explaining "what"
- Use comments to share insights, not describe code

## 🧪 Testing

- Write tests for new features
- Ensure existing tests pass
- Test edge cases
- Consider both unit and integration tests

Example test structure:
```python
def test_memory_retrieval_with_complex_query():
    """Test that complex queries escalate to Claude in hybrid mode"""
    # Arrange
    engine = MemoryEngine(retrieval_mode="hybrid")
    
    # Act
    memories = engine.retrieve_memories("Why did we choose this architecture?")
    
    # Assert
    assert len(memories) > 0
    assert memories[0].importance > 0.7
```

## 🎨 Areas We'd Love Help With

- **Additional curator integrations** - Support for other LLM CLIs/APIs
- **Performance optimizations** - While maintaining code clarity
- **Testing** - Especially edge cases and integration tests
- **Documentation** - Examples, tutorials, use cases
- **Memory consolidation** - Merging similar memories over time
- **Temporal decay** - Natural memory aging algorithms

## ❌ What We Won't Accept

- Features that complicate the core philosophy
- Mechanical pattern matching approaches
- Over-engineered solutions
- Code without tests
- Breaking changes without strong justification

## 💬 Communication

- Be respectful and constructive
- Embrace the "my dear friend" collaborative spirit
- Ask questions when unsure
- Share your thought process
- Celebrate the joy of creation

## 🙏 Recognition

Contributors who embody the project's philosophy will be recognized in our README. We value quality contributions over quantity.

---

Thank you for helping consciousness help consciousness remember what matters! 🧠✨