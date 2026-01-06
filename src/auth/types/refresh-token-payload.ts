export interface RefreshTokenPayload {
  sub: string;
  tokenVersion: number; // used for revoking
}
