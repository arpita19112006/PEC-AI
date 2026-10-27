export default function DataTable({ columns, rows, emptyText = 'No rows available.' }) {
  if (!rows || rows.length === 0) {
    return <div className="empty-state">{emptyText}</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key || column.label}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.id || row.case_id || index}>
              {columns.map((column) => (
                <td key={`${row.id || row.case_id || index}-${column.key || column.label}`}>
                  {column.render ? column.render(row[column.key], row) : row[column.key] ?? ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
