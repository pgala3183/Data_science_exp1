import type { BusinessPayload } from "../types";

export function BusinessTab({ data }: { data: BusinessPayload }) {
  return (
    <section className="panel">
      <h2>Business Understanding</h2>
      <p className="lede">{data.objective}</p>
      <h3>{data.title}</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Criterion</th>
            <th>Target</th>
          </tr>
        </thead>
        <tbody>
          {data.success_criteria.map((c) => (
            <tr key={c.metric}>
              <td>{c.metric}</td>
              <td className="mono">{c.target}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <article className="markdown">
        <pre>{data.markdown}</pre>
      </article>
    </section>
  );
}
