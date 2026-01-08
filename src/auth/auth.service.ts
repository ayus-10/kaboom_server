import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL } from './constants';
import { Repository } from 'typeorm';
import { User } from 'src/entities/user.entity';
import { InjectRepository } from '@nestjs/typeorm';

@Injectable()
export class AuthService {
  constructor(
    private readonly jwtService: JwtService,

    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async verifyRefreshToken(token: string) {
    try {
      return this.jwtService.verify(token);
    } catch {
      throw new UnauthorizedException('Invalid refresh token');
    }
  }

  async issueTokens(user: User) {
    const accessToken = this.jwtService.sign(
      {
        sub: user.id,
        email: user.email,
      },
      { expiresIn: ACCESS_TOKEN_TTL },
    );

    const refreshToken = this.jwtService.sign(
      {
        sub: user.id,
        tokenVersion: user.tokenVersion,
      },
      { expiresIn: REFRESH_TOKEN_TTL },
    );

    return { accessToken, refreshToken };
  }

  async refreshTokens(refreshToken: string) {
    try {
      const payload = await this.verifyRefreshToken(refreshToken);

      const user = await this.userRepository.findOneOrFail({
        where: { id: payload.sub },
      });

      if (user.tokenVersion !== payload.tokenVersion) {
        throw new UnauthorizedException('Token revoked');
      }

      // TODO: implement refresh token rotation here (revoke old, create new token)

      return this.issueTokens(user);
    } catch {
      throw new UnauthorizedException('User token not found');
    }
  }
}
