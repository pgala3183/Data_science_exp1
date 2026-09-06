import { useEffect, useState } from "react";
import type { QuizQuestion } from "../types";
import type { ConceptId } from "../types";
import { saveQuiz } from "../progress";

type Props = { conceptId: ConceptId; questions: QuizQuestion[] };

export function Quiz({ conceptId, questions }: Props) {
  const [answers, setAnswers] = useState<Record<string, number | null>>(
    () => Object.fromEntries(questions.map((q) => [q.id, null])),
  );
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    setAnswers(Object.fromEntries(questions.map((q) => [q.id, null])));
    setSubmitted(false);
  }, [conceptId, questions]);

  const score = questions.reduce(
    (acc, q) => acc + (answers[q.id] === q.answer ? 1 : 0),
    0,
  );

  function submit() {
    setSubmitted(true);
    saveQuiz(conceptId, score, questions.length);
  }

  return (
    <section className="quiz panel" aria-labelledby="quiz-title">
      <h2 id="quiz-title">Quick quiz</h2>
      <ol>
        {questions.map((q) => (
          <li key={q.id} className="quiz-item">
            <p className="prompt">{q.prompt}</p>
            <div className="choices">
              {q.choices.map((c, i) => {
                const selected = answers[q.id] === i;
                let cls = "choice";
                if (submitted) {
                  if (i === q.answer) cls += " correct";
                  else if (selected) cls += " wrong";
                } else if (selected) cls += " selected";
                return (
                  <button
                    key={c}
                    type="button"
                    className={cls}
                    disabled={submitted}
                    onClick={() => setAnswers((a) => ({ ...a, [q.id]: i }))}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
            {submitted && <p className="explain">{q.explain}</p>}
          </li>
        ))}
      </ol>
      {!submitted ? (
        <button
          type="button"
          className="primary"
          disabled={Object.values(answers).some((v) => v == null)}
          onClick={submit}
        >
          Check answers
        </button>
      ) : (
        <p className="score">
          Score: {score}/{questions.length} — progress saved on this device.
        </p>
      )}
    </section>
  );
}
