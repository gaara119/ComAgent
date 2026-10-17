/* Cooperative evaluation stop: retain an already sent response before exiting. */
const fs=require('node:fs');

function assertBeforeRequest(stopFile){
 if(stopFile&&fs.existsSync(stopFile)){
  const error=new Error('Evaluation stopped before the next request: '+stopFile);
  error.code='EVALUATION_STOPPED';
  throw error;
 }
}

async function collectStartedRequest(stopFile,sendAndCollect,saveResponse){
 assertBeforeRequest(stopFile);
 const response=await sendAndCollect();
 // No stop/cancellation between the real response and its evidence write.
 await saveResponse(response);
 return response;
}

module.exports={assertBeforeRequest,collectStartedRequest};
