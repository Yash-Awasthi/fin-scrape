import type { NextAuthOptions } from "next-auth";
import GithubProvider from "next-auth/providers/github";
import { config } from "./config";

export const authOptions: NextAuthOptions = {
  providers: [
    GithubProvider({
      clientId: config.auth.githubId,
      clientSecret: config.auth.githubSecret,
    }),
  ],
  secret: config.auth.secret,
  pages: {
    signIn: "/",
  },
  callbacks: {
    async session({ session, token }) {
      if (session.user && token.sub) {
        (session.user as { id?: string }).id = token.sub;
      }
      return session;
    },
  },
};
