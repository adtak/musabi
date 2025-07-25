import * as cdk from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import type { Construct } from "constructs";

export class EcrStack extends cdk.Stack {
  genTextRepository: ecr.Repository;
  genImgRepository: cdk.aws_ecr.Repository;
  selectImgRepository: cdk.aws_ecr.Repository;
  editImgRepository: cdk.aws_ecr.Repository;
  pubImgRepository: cdk.aws_ecr.Repository;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.genTextRepository = createEcrRepository(
      this,
      "GenTextRepository",
      "musabi-gen-text",
    );
    this.genImgRepository = createEcrRepository(
      this,
      "GenImgRepository",
      "musabi-gen-img",
    );
    this.selectImgRepository = createEcrRepository(
      this,
      "SelectImgRepository",
      "musabi-select-img",
    );
    this.editImgRepository = createEcrRepository(
      this,
      "EditImgRepository",
      "musabi-edit-img",
    );
    this.pubImgRepository = createEcrRepository(
      this,
      "PubImgRepository",
      "musabi-pub-img",
    );
  }
}

const createEcrRepository = (scope: Construct, id: string, name: string) => {
  return new ecr.Repository(scope, id, {
    repositoryName: name,
    removalPolicy: cdk.RemovalPolicy.DESTROY,
    lifecycleRules: [
      {
        rulePriority: 1,
        description: "Keep only one image.",
        maxImageCount: 1,
        tagStatus: ecr.TagStatus.ANY,
      },
    ],
    imageScanOnPush: false,
  });
};
