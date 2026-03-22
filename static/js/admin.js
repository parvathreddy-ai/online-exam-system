function addQuestion() {
    const container = document.getElementById("questionsContainer");

    const block = document.createElement("div");
    block.classList.add("question-block");

    block.innerHTML = `
        <textarea name="question_text[]" placeholder="Enter Question" required></textarea>

        <input type="text" name="option1[]" placeholder="Option 1" required>
        <input type="text" name="option2[]" placeholder="Option 2" required>
        <input type="text" name="option3[]" placeholder="Option 3" required>
        <input type="text" name="option4[]" placeholder="Option 4" required>

        <input type="text" name="correct_answer[]" placeholder="Correct Answer" required>
        <hr>
    `;

    container.appendChild(block);
}