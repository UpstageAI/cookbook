import * as dotenv from "dotenv";
import { AwsRegion, regionToAirportCode } from "./commons";

// Load environment variables from .env file
dotenv.config();

export interface Account {
  readonly accountId: string;
  readonly region: AwsRegion;
  readonly airportCode: string;
}

/**
 * Validates if the provided region string is a valid AWS region
 * @param region Region string to validate
 * @returns The matching AwsRegion enum value
 * @throws Error if the region is invalid
 */
function validateAndGetRegion(region: string): AwsRegion {
  // Check if the region exists in AwsRegion enum values
  const awsRegions = Object.values(AwsRegion);
  const matchingRegion = awsRegions.find((r) => r === region);

  if (!matchingRegion) {
    const validRegions = awsRegions.join(", ");
    throw new Error(
      `Invalid AWS region: ${region}. Valid regions are: ${validRegions}`
    );
  }

  // Find the enum key for this region value
  const regionKey = Object.keys(AwsRegion).find(
    (key) => AwsRegion[key as keyof typeof AwsRegion] === region
  );

  if (!regionKey) {
    throw new Error(`Could not find enum key for region: ${region}`);
  }

  return AwsRegion[regionKey as keyof typeof AwsRegion];
}

// Validate environment variables
if (!process.env.AWS_ACCOUNT_ID) {
  throw new Error("AWS_ACCOUNT_ID is not set in environment variables");
}

if (!process.env.AWS_REGION) {
  throw new Error("AWS_REGION is not set in environment variables");
}

// Validate and get the AWS region
const awsRegion = validateAndGetRegion(process.env.AWS_REGION);

/**
 * Default account configuration for Upstage
 * Uses AWS_ACCOUNT_ID and AWS_REGION from environment variables
 */
export const UPSTAGE_ACCOUNT: Account = {
  accountId: process.env.AWS_ACCOUNT_ID,
  region: awsRegion,
  airportCode: regionToAirportCode(awsRegion),
};
