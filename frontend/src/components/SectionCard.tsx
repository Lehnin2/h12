import { motion } from "framer-motion";
import type { PropsWithChildren, ReactNode } from "react";
import { UiIcon } from "./UiIcon";

interface SectionCardProps extends PropsWithChildren {
  eyebrow?: string;
  title: string;
  aside?: ReactNode;
  icon?: any; // Using any for icon name to avoid circular dependency or complex type mapping for now
  duotone?: boolean;
}

export function SectionCard({ eyebrow, title, aside, icon, duotone = true, children }: SectionCardProps) {
  return (
    <motion.section
      className="section-card"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="section-card__header">
        <div className="section-card__title-group">
          {icon && (
            <div className="section-card__icon">
              <UiIcon name={icon} duotone={duotone} />
            </div>
          )}
          <div>
            {eyebrow ? <p className="section-card__eyebrow">{eyebrow}</p> : null}
            <h2>{title}</h2>
          </div>
        </div>
        {aside ? <div className="section-card__aside">{aside}</div> : null}
      </div>
      {children}
    </motion.section>
  );
}

