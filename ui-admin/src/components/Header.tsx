import type { ReactNode } from 'react';

interface HeaderProps {
  title: string;
  actions?: ReactNode;
}

const Header = ({ title, actions }: HeaderProps) => {
  return (
    <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
      <h2 className="text-2xl font-semibold text-white">{title}</h2>
      {actions && <div className="flex items-center space-x-2">{actions}</div>}
    </div>
  );
};

export default Header;
