import { SageMakerRuntimeClient, InvokeEndpointWithResponseStreamCommand } from "@aws-sdk/client-sagemaker-runtime";
 


const client = new SageMakerRuntimeClient({ region: process.env.AWS_REGION });
export const handler = awslambda.streamifyResponse(async (event, responseStream) => {
  try {
    console.log("Received event:", JSON.stringify(event, null, 2));

    // Check for bearer token in header
    const authHeader = event.headers?.Authorization || event.headers?.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ') || authHeader.substring(7) !== process.env.API_KEY_VALUE) {
      console.error('Authorization failed: Invalid or missing bearer token');
      responseStream.write(JSON.stringify({
        statusCode: 401,
        body: JSON.stringify({ 
          error: 'Permission denied', 
          details: 'Invalid or missing authentication token' 
        })
      }));
      responseStream.end();
      return;
    }

    const endpointName = process.env.SAGEMAKER_ENDPOINT_NAME;

    // Ensure `event.body` exists before parsing
    const inputPayload = JSON.parse(event.body);
    const jsonString = JSON.stringify(inputPayload);
    
    console.log("Sending to SageMaker:", jsonString);

    const params = {
      EndpointName: endpointName,
      Body: Buffer.from(jsonString, 'utf-8'),
      ContentType: 'application/json'
    };

    const command = new InvokeEndpointWithResponseStreamCommand(params);
    const response = await client.send(command);

    console.log("SageMaker Response:", JSON.stringify(response, null, 2));

    // Handle the streaming response - in SDK v3, Body is an async iterable
    try {
      for await (const chunk of response.Body) {
        // Each chunk contains PayloadPart property with Base64-encoded data
        if (chunk && chunk.PayloadPart && chunk.PayloadPart.Bytes) {
          responseStream.write(chunk.PayloadPart.Bytes);
        }
      }
      responseStream.end();
    } catch (streamError) {
      console.error('Error processing SageMaker response stream:', streamError);
      responseStream.write(JSON.stringify({
        statusCode: 500,
        body: JSON.stringify({ 
          error: 'Error processing SageMaker response stream', 
          details: streamError.message 
        })
      }));
      responseStream.end();
    }

  } catch (error) {
    console.error('Error invoking SageMaker endpoint:', error);
    responseStream.write(JSON.stringify({
      statusCode: 500,
      body: JSON.stringify({ 
        error: 'Error invoking SageMaker endpoint', 
        details: error.message 
      })
    }));
    responseStream.end();
  }
});
