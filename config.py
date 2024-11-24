answer_examples = [
    {
        "input": "How do I create a character controller in Unity?",
        "answer": """To create a character controller in Unity, follow these steps:

1. Go to the Unity Asset Store and import the Standard Assets package, which includes a Character Controller component.
2. Create an empty GameObject in your scene and add the Character Controller component to it.
3. Adjust the Character Controller settings, such as Height, Radius, and Step Offset, to match your character’s needs.
4. Write a custom script to control the character’s movement using Unity's Input system.
5. Attach the script to the GameObject and customize the movement parameters.

For detailed guidance, refer to the character setup section in the 'Unity Game Development in 24 Hours' guide.
        """
    },
    {
        "input": "What are some best practices for optimizing performance in Unity?",
        "answer": """To optimize performance in Unity, consider the following best practices:

- Use object pooling to reduce instantiation and destruction overhead.
- Limit the number of active GameObjects in the scene to keep the frame rate high.
- Use LOD (Level of Detail) for models to display simpler models at farther distances.
- Optimize your scripts by reducing the number of Update calls, using coroutines, and caching component references.
- Adjust lighting settings and use baked lighting for static objects where possible.
- Use the Profiler in Unity to identify bottlenecks in performance.

For a more comprehensive list, refer to the optimization chapter in 'Unity Game Development in 24 Hours'.
        """
    },
]
