import {
  Controller,
  Get,
  Req,
  UseGuards,
  Res,
  Post,
  UnauthorizedException,
} from '@nestjs/common';
import { AuthService } from './auth.service';
import { GoogleAuthGuard } from './guards/google-auth.guard';
import type { GoogleAuthRequest } from './types/google-auth-request';
import type { CookieOptions, Request, Response } from 'express';
import { ConfigService } from '@nestjs/config';
import { UserService } from 'src/user/user.service';

@Controller('auth')
export class AuthController {
  private readonly clientUrl: string;
  private readonly cookieOptions: CookieOptions = {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    path: '/auth/refresh',
    maxAge: 7 * 24 * 60 * 60 * 1000,
  };

  constructor(
    private readonly authService: AuthService,
    private readonly configService: ConfigService,
    private readonly userService: UserService,
  ) {
    this.clientUrl = this.configService.getOrThrow('CLIENT_URL');
  }

  @Get('google')
  @UseGuards(GoogleAuthGuard)
  async googleAuth() {}

  @Get('google/callback')
  @UseGuards(GoogleAuthGuard)
  async googleAuthRedirect(
    @Req() req: GoogleAuthRequest,
    @Res() res: Response,
  ) {
    const googleProfile = req.user;

    const user = await this.userService.findOrCreateFromGoogle({
      email: googleProfile.email,
      firstName: googleProfile.firstName,
      lastName: googleProfile.lastName,
      picture: googleProfile.picture,
    });

    const tokens = await this.authService.issueTokens(user);

    res.cookie('refresh_token', tokens.refreshToken, this.cookieOptions);

    return res.redirect(`${this.clientUrl}?token=${tokens.accessToken}`);
  }

  @Post('refresh')
  async refresh(@Req() req: Request, @Res() res: Response) {
    const refreshToken = req.cookies?.refresh_token;
    if (!refreshToken) {
      throw new UnauthorizedException('Refresh token missing');
    }

    const tokens = await this.authService.refreshTokens(refreshToken);

    res.cookie('refresh_token', tokens.refreshToken, this.cookieOptions);

    return res.json({ accessToken: tokens.accessToken });
  }
}
