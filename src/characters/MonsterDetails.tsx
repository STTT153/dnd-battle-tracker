import type { MonsterStats } from './models';
import styles from './Characters.module.css';

const signed = (value: number) => value >= 0 ? `+${value}` : String(value);
export function MonsterDetails({ stats }: { stats: MonsterStats }) {
  const abilities = Object.entries(stats.abilities).map(([key, value]) => {
    const label = ({ strength: '力量', dexterity: '敏捷', constitution: '体质', intelligence: '智力', wisdom: '感知', charisma: '魅力' } as Record<string, string>)[key];
    return `${label} ${value.score}  调整 ${signed(value.modifier)}  豁免 ${signed(value.savingThrow)}`;
  }).join('\n');
  const defenses = [stats.vulnerabilities, stats.resistances, stats.damageImmunities, stats.conditionImmunities];
  const lines = [
    ['英文名', stats.englishName], ['体型、种类与阵营', stats.classification], ['AC', stats.armorClass], ['速度', stats.speed],
    ['属性 · 调整 · 豁免', abilities], ['技能', stats.skills.map((skill) => `${skill.name}${signed(skill.bonus)}`).join('、')],
    ['易伤', stats.vulnerabilities.join('、')], ['抗性', stats.resistances.join('、')],
    ['伤害免疫', stats.damageImmunities.join('、')], ['状态免疫', stats.conditionImmunities.join('、')],
    ['易伤 · 抗性 · 免疫', defenses.some((entries) => entries.length) ? '' : stats.defenses.join('\n')],
    ['感官', stats.senses], ['语言', stats.languages.join('、')],
    ['CR', [stats.challengeRating, stats.experiencePoints === null ? '' : `XP ${stats.experiencePoints.toLocaleString()}`,
      stats.proficiencyBonus === null ? '' : `PB ${signed(stats.proficiencyBonus)}`].filter(Boolean).join(' · ')],
    ['特质', stats.traits.join('\n\n')],
  ];
  return <dl className={styles.details}>{lines.filter(([, value]) => value).map(([title, value]) =>
    <div key={title}><dt>{title}</dt><dd>{value}</dd></div>)}</dl>;
}
