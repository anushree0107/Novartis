import { ReactNode } from 'react';

// Simple cn utility
const cn = (...classes: (string | undefined | false)[]) => classes.filter(Boolean).join(' ');

interface CardProps {
    children: ReactNode;
    className?: string;
}

export function Card({ children, className = '' }: CardProps) {
    return (
        <div className={cn("rounded-xl border bg-gray-800/50 text-white", className)}>
            {children}
        </div>
    );
}

interface CardHeaderProps {
    children: ReactNode;
    className?: string;
}

export function CardHeader({ children, className = '' }: CardHeaderProps) {
    return (
        <div className={cn("flex flex-col space-y-1.5 p-4", className)}>
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
        <h3 className={cn("text-lg font-semibold leading-none tracking-tight text-white", className)}>
            {children}
        </h3>
    );
}

interface CardContentProps {
    children: ReactNode;
    className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
    return (
        <div className={cn("p-4 pt-0", className)}>
            {children}
        </div>
    );
}
