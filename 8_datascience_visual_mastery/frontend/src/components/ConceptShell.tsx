import { type PropsWithChildren } from "react";
import { Link } from "react-router-dom";

type Props = { title: string };

export function ConceptShell({ title, children }: PropsWithChildren<Props>) {
  return (
    <div className="concept-page">
      <nav className="crumb">
        <Link to="/">← All concepts</Link>
      </nav>
      <h1>{title}</h1>
      {children}
    </div>
  );
}
