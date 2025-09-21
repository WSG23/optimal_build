import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Sources' },
  { to: '/documents', label: 'Documents' },
  { to: '/clauses', label: 'Clauses' },
  { to: '/rules', label: 'Rules Review' },
  { to: '/diffs', label: 'Diffs' }
];

const Sidebar = () => {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800">
      <div className="px-6 py-4 border-b border-slate-800">
        <h1 className="text-lg font-semibold">Optimal Build Admin</h1>
        <p className="text-xs text-slate-400">Review compliance content</p>
      </div>
      <nav className="flex flex-col px-2 py-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${
                isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
