import { Controller, Get, Post, Req, UseGuards } from '@nestjs/common';
import { UserService } from './user.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import type { JwtAuthRequest } from './types/jwt-auth-request';

@Controller('users')
@UseGuards(JwtAuthGuard)
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get('me')
  async getMe(@Req() req: JwtAuthRequest) {
    return this.userService.findById(req.user.userId);
  }

  @Post('logout')
  async logoutEverywhere(@Req() req: JwtAuthRequest) {
    await this.userService.revokeAllSessions(req.user.userId);
    return { success: true };
  }
}
