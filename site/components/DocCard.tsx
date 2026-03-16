import Link from "next/link";
import {
  MessageSquare,
  Wrench,
  Shield,
  BarChart3,
  Zap,
  Target,
  Book,
  Lightbulb,
  type LucideIcon,
} from "lucide-react";

const iconMap: Record<string, LucideIcon> = {
  message: MessageSquare,
  wrench: Wrench,
  shield: Shield,
  chart: BarChart3,
  bolt: Zap,
  target: Target,
  book: Book,
  lightbulb: Lightbulb,
};

interface DocCardProps {
  title: string;
  description: string;
  icon: keyof typeof iconMap;
  href: string;
  external?: boolean;
}

export function DocCard({ title, description, icon, href, external }: DocCardProps) {
  const Icon = iconMap[icon] ?? MessageSquare;

  const content = (
    <div className="flex h-full flex-col rounded-xl border border-zinc-700 bg-zinc-800/50 p-6 shadow-sm transition-all hover:border-violet-500/50">
      <Icon className="mb-3 h-6 w-6 text-violet-400" />
      <h3 className="font-semibold text-zinc-100 mb-2">{title}</h3>
      <p className="text-sm text-zinc-400 flex-1">{description}</p>
      <span className="mt-3 text-sm font-medium text-violet-400">Learn more →</span>
    </div>
  );

  if (external) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="block h-full"
      >
        {content}
      </a>
    );
  }

  return <Link href={href} className="block h-full">{content}</Link>;
}
