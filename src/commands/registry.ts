import type { IconName } from '../icons/Icon';
import type { CharacterDraft } from '../stores/sessionStore';
import type { CharacterKind, MonsterDefinition } from '../characters/models';

export interface CommandIds {
  'combat.start': undefined;
  'combat.nextTurn': undefined;
  'combat.reset': undefined;
  'combat.stop': undefined;
  'combat.sort': undefined;
  'combat.moveUp': undefined;
  'combat.moveDown': undefined;
  'combat.damage': undefined;
  'combat.heal': undefined;
  'combat.setAmount': string;
  'character.addPlayer': undefined;
  'character.addNpc': undefined;
  'character.addMonster': undefined;
  'character.addManualMonster': undefined;
  'character.select': string;
  'character.updateDraft': Partial<CharacterDraft>;
  'character.submit': undefined;
  'character.copy': undefined;
  'character.paste': undefined;
  'character.remove': undefined;
  'character.quickRemove': undefined;
  'character.filter': CharacterKind | 'all';
  'monster.choose': MonsterDefinition;
  'monster.closePicker': undefined;
  'monster.retry': undefined;
  'workbench.view.combat': undefined;
  'workbench.view.characters': undefined;
  'workbench.view.monsters': undefined;
  'workbench.toggleInspector': undefined;
}

export type CommandId = keyof CommandIds;
export type SimpleCommandId = { [K in CommandId]: CommandIds[K] extends undefined ? K : never }[CommandId];
export type CommandArgs<K extends CommandId> = CommandIds[K] extends undefined
  ? [payload?: undefined] : [payload: CommandIds[K]];
export interface Command<K extends CommandId = CommandId> {
  id: K;
  title: string;
  icon: IconName;
  availability?: () => { enabled: boolean; reason?: string };
  execute: (payload: CommandIds[K]) => void | boolean | Promise<void | boolean>;
}

type StoredCommand = Omit<Command, 'execute'> & { execute: (payload: unknown) => void | boolean | Promise<void | boolean> };

export class CommandRegistry {
  private commands = new Map<CommandId, StoredCommand>();

  constructor(private isBlocked = () => false, private onError: (error: unknown) => void = (error: unknown) => { throw error; }) {}

  register<K extends CommandId>(command: Command<K>): () => void {
    if (this.commands.has(command.id)) throw new Error(`命令已注册：${command.id}`);
    const stored: StoredCommand = { ...command, execute: (payload) => command.execute(payload as CommandIds[K]) };
    this.commands.set(command.id, stored);
    return () => {
      if (this.commands.get(command.id) === stored) this.commands.delete(command.id);
    };
  }

  get(id: CommandId) {
    const command = this.commands.get(id);
    if (!command) throw new Error(`命令未注册：${id}`);
    return command;
  }

  getAvailability(id: CommandId) {
    const command = this.get(id);
    if (this.isBlocked()) return { enabled: false, reason: '请先完成当前确认。' };
    return command.availability?.() ?? { enabled: true };
  }

  async execute<K extends CommandId>(id: K, ...args: CommandArgs<K>): Promise<boolean> {
    const command = this.get(id);
    if (!this.getAvailability(id).enabled) return false;
    try {
      return (await command.execute(args[0])) !== false;
    } catch (error) {
      this.onError(error);
      return false;
    }
  }
}
