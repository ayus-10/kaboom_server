import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { GoogleProfile } from './types/google-profile';

@Injectable()
export class UserService {
  constructor(private readonly prismaService: PrismaService) {}

  async findOrCreateFromGoogle(profile: GoogleProfile) {
    return this.prismaService.user.upsert({
      where: { email: profile.email },
      update: {},
      create: {
        email: profile.email,
        firstName: profile.firstName,
        lastName: profile.lastName,
        avatarUrl: profile.picture,
      },
    });
  }

  async findById(userId: string) {
    return this.prismaService.user.findUnique({
      where: { id: userId },
    });
  }

  async revokeAllSessions(userId: string) {
    await this.prismaService.user.update({
      where: { id: userId },
      data: {
        tokenVersion: { increment: 1 },
      },
    });

    await this.prismaService.session.updateMany({
      where: { userId },
      data: { isRevoked: true },
    });
  }
}
