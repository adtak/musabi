import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";

export class IacV2Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const inputBucket = new s3.Bucket(this, "InputMusabiBucket", {
      bucketName: "input-musabi-bot-bucket",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      bucketKeyEnabled: false,
      encryption: s3.BucketEncryption.S3_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      publicReadAccess: false,
      versioned: false,
    });

    const outputBucket = new s3.Bucket(this, "OutputMusabiBucket", {
      bucketName: "output-musabi-bot-bucket",
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      bucketKeyEnabled: false,
      encryption: s3.BucketEncryption.S3_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      publicReadAccess: false,
      versioned: false,
    });

    const generateImageRepository = new cdk.aws_ecr.Repository(
      this,
      "GenerateImageRepository",
      {
        repositoryName: "generate-image-repository",
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        lifecycleRules: [
          {
            rulePriority: 1,
            description: "Keep only one image.",
            maxImageCount: 1,
            tagStatus: cdk.aws_ecr.TagStatus.ANY,
          },
        ],
        imageScanOnPush: false,
      }
    );

    const generateDishFunction = new cdk.aws_lambda.Function(
      this,
      "GenerateDishLambda",
      {
        runtime: cdk.aws_lambda.Runtime.PYTHON_3_9,
        handler: "generate_dish.handler",
        code: cdk.aws_lambda.Code.fromAsset("iac-v1/musabi_iac/lambda_handler"),
        memorySize: 256,
        timeout: cdk.Duration.minutes(3),
        environment: {
          ParameterName: "/openai/musabi/api_key",
        },
      }
    );

    generateDishFunction.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: cdk.aws_iam.Effect.ALLOW,
        actions: ["ssm:GetParameter"],
        resources: [
          `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/openai/musabi/*`,
        ],
      })
    );

    const publishImageFunction = new cdk.aws_lambda.Function(
      this,
      "PublishImageLambda",
      {
        runtime: cdk.aws_lambda.Runtime.PYTHON_3_9,
        handler: "publish_image.handler",
        code: cdk.aws_lambda.Code.fromAsset("iac-v1/musabi_iac/lambda_handler"),
        memorySize: 256,
        timeout: cdk.Duration.minutes(3),
        environment: {
          ImageBucket: outputBucket.bucketName,
          ParameterName: "/meta/musabi/api_key",
        },
      }
    );

    publishImageFunction.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: cdk.aws_iam.Effect.ALLOW,
        actions: ["s3:GetObject"],
        resources: [outputBucket.arnForObjects("*")],
      })
    );

    publishImageFunction.addToRolePolicy(
      new cdk.aws_iam.PolicyStatement({
        effect: cdk.aws_iam.Effect.ALLOW,
        actions: ["ssm:GetParameter"],
        resources: [
          `arn:aws:ssm:ap-northeast-1:${cdk.Aws.ACCOUNT_ID}:parameter/meta/musabi/*`,
        ],
      })
    );

    const generateDishStep = new cdk.aws_stepfunctions_tasks.LambdaInvoke(
      this,
      "GenerateDish",
      {
        lambdaFunction: generateDishFunction,
        integrationPattern:
          cdk.aws_stepfunctions.IntegrationPattern.REQUEST_RESPONSE,
        resultPath: "$.GenerateDishResults",
      }
    );

    const processingStep = new cdk.aws_stepfunctions.CustomState(
      this,
      "SagemakerProcessingTask",
      {
        stateJson: {
          Type: "Task",
          Resource: "arn:aws:states:::sagemaker:createProcessingJob.sync",
          Parameters: {
            AppSpecification: {
              ImageUri: generateImageRepository.repositoryUriForTag("latest"),
            },
            Environment: {
              "PROMPT.$":
                "States.Format('{}, {}', $.GenerateDishResults.Payload.EngDishName, $.Prompt)",
              "NEGATIVE_PROMPT.$": "$.NegativePrompt",
              "WIDTH.$": "$.Width",
              "HEIGHT.$": "$.Height",
              "DISH_NAME.$": "$.GenerateDishResults.Payload.DishName",
            },
            ProcessingJobName:
              "States.Format('PreprocessingJob-{}', States.UUID())",
            ProcessingResources: {
              ClusterConfig: {
                InstanceCount: 1,
                InstanceType: "ml.p3.2xlarge",
                VolumeSizeInGB: 1,
              },
            },
            ProcessingInputs: [
              {
                InputName: "PreprocessingJobInput",
                S3Input: {
                  LocalPath: "/opt/ml/processing/input",
                  S3CompressionType: "None",
                  S3DataType: "S3Prefix",
                  S3InputMode: "File",
                  S3Uri: inputBucket.urlForObject(),
                },
              },
            ],
            ProcessingOutputConfig: {
              Outputs: [
                {
                  OutputName: "PreprocessingJobOutput",
                  S3Output: {
                    LocalPath: "/opt/ml/processing/output",
                    S3UploadMode: "EndOfJob",
                    S3Uri: `States.Format('${outputBucket.s3UrlForObject()}/{}', $$.Execution.Name)`,
                  },
                },
              ],
            },
            RoleArn: "arn:aws:iam::ACCOUNT_ID:role/SageMakerRole",
            StoppingCondition: { MaxRuntimeInSeconds: 600 },
          },
          ResultPath: "$.PreprocessingResults",
        },
      }
    );

    const publishImageStep = new cdk.aws_stepfunctions_tasks.LambdaInvoke(
      this,
      "PublishImage",
      {
        lambdaFunction: publishImageFunction,
        payload: cdk.aws_stepfunctions.TaskInput.fromObject({
          TitleImageKey: "States.Format('{}/0_image_1.png', $$.Execution.Name)",
          ImageKey: "States.Format('{}/0_image_2.png', $$.Execution.Name)",
          DishName: "$.GenerateDishResults.Payload.DishName",
          Recipe: "$.GenerateDishResults.Payload.Recipe",
          DryRun: "$.DryRun",
        }),
        integrationPattern:
          cdk.aws_stepfunctions.IntegrationPattern.REQUEST_RESPONSE,
      }
    );

    const successState = new cdk.aws_stepfunctions.Succeed(this, "Succeded");

    const definition = generateDishStep
      .next(processingStep)
      .next(publishImageStep)
      .next(successState);

    const stateMachine = new cdk.aws_stepfunctions.StateMachine(
      this,
      "MusabiStateMachine",
      {
        stateMachineName: "musabi-bot-statemachine",
        definition,
        timeout: cdk.Duration.minutes(30),
      }
    );

    new cdk.aws_events.Rule(this, "MusabiEventsRule", {
      schedule: cdk.aws_events.Schedule.cron({ hour: "*/12", minute: "0" }),
      targets: [
        new cdk.aws_events_targets.SfnStateMachine(stateMachine, {
          input: cdk.aws_events.RuleTargetInput.fromObject({
            Comment: "Insert your JSON here",
            Prompt: [
              "best quality",
              "ultra high res",
              "(photorealistic:1.4)",
              "a very delicious-looking cuisine",
              "a very delicious-looking dish",
            ].join(", "),
            NegativePrompt: [
              "paintings",
              "sketches",
              "(worst quality:2)",
              "(low quality:2)",
              "(normal quality:2)",
              "lowres",
              "normal quality",
              "((monochrome))",
              "((grayscale))",
            ].join(", "),
            Width: "800",
            Height: "800",
            DryRun: false,
          }),
          maxEventAge: cdk.Duration.minutes(15),
          retryAttempts: 0,
        }),
      ],
    });
  }
}
