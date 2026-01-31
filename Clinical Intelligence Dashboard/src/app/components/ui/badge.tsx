import { ReactNode, ButtonHTMLAttributes } from 'react';

// Re-export lucide icons for convenience
export { Play, RotateCcw, Download, ChevronDown, ChevronUp } from 'lucide-react';

// Simple cn utility inline
const cn = (...classes: (string | undefined | false)[]) => classes.filter(Boolean).join(' ');

interface BadgeProps {
    children: ReactNode;
    variant?: 'default' | 'outline';
    className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
    const baseClasses = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors';
    const variantClasses = variant === 'outline'
        ? 'border border-gray-600 bg-transparent text-gray-300'
        : 'bg-gray-700 text-gray-200';

    return (
        <span className={cn(baseClasses, variantClasses, className)}>
            {children}
        </span>
    );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    children: ReactNode;
    variant?: 'default' | 'outline' | 'ghost';
    size?: 'default' | 'sm';
    className?: string;
}

export function Button({
    children,
    variant = 'default',
    size = 'default',
    className = '',
    disabled,
    ...props
}: ButtonProps) {
    const baseClasses = 'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none';

    const sizeClasses = size === 'sm' ? 'px-3 py-1.5 text-sm' : 'px-4 py-2 text-sm';

    const variantClasses = {
        default: 'bg-cyan-500 text-white hover:bg-cyan-400',
        outline: 'border border-gray-600 bg-transparent text-gray-300 hover:bg-gray-800',
        ghost: 'bg-transparent text-gray-400 hover:bg-gray-800 hover:text-gray-200',
    }[variant];

    const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';

    return (
        <button
            className={cn(baseClasses, sizeClasses, variantClasses, disabledClasses, className)}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
}
