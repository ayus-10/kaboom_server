import { Request } from 'express';
import { GoogleUserDto } from '../dtos/google-user.dto';

export interface GoogleAuthRequest extends Request {
  user: GoogleUserDto;
}
