import {
  Entity,
  PrimaryColumn,
  Column,
  ManyToOne,
  Index,
  CreateDateColumn,
  UpdateDateColumn,
  JoinColumn,
} from 'typeorm';
import { User } from './user.entity';

@Entity()
export class UserToken {
  @PrimaryColumn('varchar')
  id: string;

  @Column('varchar')
  @Index()
  userId: string;

  @ManyToOne(() => User, (user) => user.tokens, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'userId' })
  user: User;

  @Column()
  refreshTokenHash: string;

  @Column({ default: false })
  isRevoked: boolean;

  @Column({ nullable: true })
  ipAddress?: string;

  @Column()
  expiresAt: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
