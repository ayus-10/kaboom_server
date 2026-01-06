import { Request } from 'express';

export interface JwtAuthRequest extends Request {
  user: {
    userId: string;
    email: string;
  };
}
