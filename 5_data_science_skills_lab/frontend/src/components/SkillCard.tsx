import { Link } from "react-router-dom";
import type { Skill } from "../types";

type Props = {
  skill: Skill;
  done: boolean;
};

export function SkillCard({ skill, done }: Props) {
  return (
    <article className={`card ${done ? "done" : ""}`}>
      <Link to={`/skills/${skill.id}`}>
        <div className="badges">
          <span className="badge cat">{skill.category}</span>
          <span className="badge diff">{skill.difficulty}</span>
          {done && <span className="badge ok">Done</span>}
        </div>
        <h2>{skill.name}</h2>
        <p>{skill.description}</p>
        <p className="dataset">Dataset: {skill.dataset}</p>
      </Link>
    </article>
  );
}
