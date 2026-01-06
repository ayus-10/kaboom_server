export class RefreshTokenPayload {
  sub: string;
  tokenVersion: number; // used for revoking
}
