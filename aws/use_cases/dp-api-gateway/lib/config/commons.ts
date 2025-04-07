export enum AwsRegion {
  // North America
  IAD = "us-east-1", // US East (N. Virginia)
  CMH = "us-east-2", // US East (Ohio)
  PDX = "us-west-2", // US West (Oregon)
  SFO = "us-west-1", // US West (N. California)
  YUL = "ca-central-1", // Canada (Central)

  // South America
  GRU = "sa-east-1", // South America (São Paulo)

  // Europe
  DUB = "eu-west-1", // Europe (Ireland)
  LHR = "eu-west-2", // Europe (London)
  CDG = "eu-west-3", // Europe (Paris)
  ARN = "eu-north-1", // Europe (Stockholm)
  FRA = "eu-central-1", // Europe (Frankfurt)
  MXP = "eu-south-1", // Europe (Milan)
  ZRH = "eu-central-2", // Europe (Zurich)

  // Asia Pacific
  ICN = "ap-northeast-2", // Asia Pacific (Seoul)
  NRT = "ap-northeast-1", // Asia Pacific (Tokyo)
  HKG = "ap-east-1", // Asia Pacific (Hong Kong)
  BOM = "ap-south-1", // Asia Pacific (Mumbai)
  SIN = "ap-southeast-1", // Asia Pacific (Singapore)
  SYD = "ap-southeast-2", // Asia Pacific (Sydney)
  CGK = "ap-southeast-3", // Asia Pacific (Jakarta)
  HYD = "ap-south-2", // Asia Pacific (Hyderabad)
  MFM = "ap-southeast-4", // Asia Pacific (Melbourne)

  // Middle East
  BAH = "me-south-1", // Middle East (Bahrain)
  AUH = "me-central-1", // Middle East (UAE)

  // Africa
  CPT = "af-south-1", // Africa (Cape Town)
}

const RegionToAirportCode = new Map<AwsRegion, string>([
  // North America
  [AwsRegion.IAD, "IAD"],
  [AwsRegion.CMH, "CMH"],
  [AwsRegion.PDX, "PDX"],
  [AwsRegion.SFO, "SFO"],
  [AwsRegion.YUL, "YUL"],

  // South America
  [AwsRegion.GRU, "GRU"],

  // Europe
  [AwsRegion.DUB, "DUB"],
  [AwsRegion.LHR, "LHR"],
  [AwsRegion.CDG, "CDG"],
  [AwsRegion.ARN, "ARN"],
  [AwsRegion.FRA, "FRA"],
  [AwsRegion.MXP, "MXP"],
  [AwsRegion.ZRH, "ZRH"],

  // Asia Pacific
  [AwsRegion.ICN, "ICN"],
  [AwsRegion.NRT, "NRT"],
  [AwsRegion.HKG, "HKG"],
  [AwsRegion.BOM, "BOM"],
  [AwsRegion.SIN, "SIN"],
  [AwsRegion.SYD, "SYD"],
  [AwsRegion.CGK, "CGK"],
  [AwsRegion.HYD, "HYD"],
  [AwsRegion.MFM, "MFM"],

  // Middle East
  [AwsRegion.BAH, "BAH"],
  [AwsRegion.AUH, "AUH"],

  // Africa
  [AwsRegion.CPT, "CPT"],
]);

export function regionToAirportCode(region: AwsRegion): string {
  return RegionToAirportCode.get(region) || "ICN";
}
