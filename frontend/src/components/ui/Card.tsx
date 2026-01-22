import type { ReactNode, HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: 'sm' | 'md' | 'lg';
}

const paddingStyles = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export function Card({
  children,
  padding = 'md',
  className = '',
  ...props
}: CardProps) {
  return (
    <div
      className={`
        bg-slate-800 border border-slate-700 rounded-2xl
        shadow-xl shadow-black/20
        ${paddingStyles[padding]}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardTitleProps {
  children: ReactNode;
  className?: string;
}

export function CardTitle({ children, className = '' }: CardTitleProps) {
  return (
    <h2 className={`text-2xl font-bold text-white mb-2 ${className}`}>
      {children}
    </h2>
  );
}

export function CardDescription({ children, className = '' }: CardTitleProps) {
  return (
    <p className={`text-slate-400 mb-6 ${className}`}>
      {children}
    </p>
  );
}
