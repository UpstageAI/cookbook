import { Account, UPSTAGE_ACCOUNT } from "./accounts";

interface InstanceType {
  modelPackageName: string;
  instanceType: string;
}

const G6_Instance = {
  modelPackageName:
    "upstage-document-parse-cuda12--d0c44ece666c340083b67fd682d35595",
  instanceType: "ml.g6.xlarge",
};

const G5_Instance = {
  modelPackageName:
    "upstage-document-parse-cuda11--a2f49bd4aea13c7b94ba3c034aa524a7",
  instanceType: "ml.g5.xlarge",
};

export interface Environment {
  readonly name: string;
  readonly account: Account;
  readonly instanceType: InstanceType;
}
export const env = {
  name: "upstage-document-parse",
  account: UPSTAGE_ACCOUNT,
  instanceType: G5_Instance,
};
