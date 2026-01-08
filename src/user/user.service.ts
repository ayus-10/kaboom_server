import {
  Injectable,
  InternalServerErrorException,
  NotFoundException,
} from '@nestjs/common';
import { GoogleProfile } from './types/google-profile';
import { Repository } from 'typeorm';
import { User } from 'src/entities/user.entity';
import { InjectRepository } from '@nestjs/typeorm';
import { UserToken } from 'src/entities/user-token.entity';
import { DataSource } from 'typeorm/browser';

@Injectable()
export class UserService {
  constructor(
    private readonly dataSource: DataSource,

    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async findOrCreateFromGoogle(profile: GoogleProfile) {
    try {
      await this.userRepository.upsert(
        {
          email: profile.email,
          firstName: profile.firstName,
          lastName: profile.lastName,
          avatarUrl: profile.picture,
        },
        {
          conflictPaths: ['email'],
          skipUpdateIfNoValuesChanged: true,
        },
      );

      return await this.userRepository.findOneOrFail({
        where: { email: profile.email },
      });
    } catch {
      throw new InternalServerErrorException('Unable to save user data');
    }
  }

  async findById(userId: string) {
    try {
      return this.userRepository.findOneOrFail({
        where: { id: userId },
      });
    } catch {
      throw new NotFoundException('User not found');
    }
  }

  async revokeAllTokens(userId: string) {
    await this.dataSource.transaction(async (manager) => {
      await manager.increment(User, { id: userId }, 'tokenVersion', 1);
      await manager.update(UserToken, { userId }, { isRevoked: true });
    });
  }
}
