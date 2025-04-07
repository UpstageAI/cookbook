import { Account, UPSTAGE_ACCOUNT } from "./accounts";

export interface Environment {
  readonly account: Account;
  readonly instanceType: string;
  readonly modelPackageName: string;
}
export const env = {
  account: UPSTAGE_ACCOUNT,
  instanceType: "ml.p4d.24xlarge",
  modelPackageName: "solar-pro-250312-r1-890c5af6f811399bab5147c2b6803442",
};
