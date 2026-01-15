from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio
from sqlalchemy.orm import Session

from app.schemas.models import DeepSeekResponse, DeepSeekRequest
from app.servers.DeepDeekServer import DeepDeekServer
from app.dependencies.database import get_db
from app.models.conversation import Conversation

router = APIRouter(tags=["DeepSeek"])

deepseek_server = DeepDeekServer()

@router.post("/deepseek")
async def query_deepseek(
    request: DeepSeekRequest,
    db: Session = Depends(get_db)
):
    try:
        if request.stream:
            full_answer = []
            
            async def generate():
                try:
                    async for chunk in deepseek_server.query_astream(request.question):
                        if chunk:
                            full_answer.append(chunk)
                            yield chunk
                    
                    complete_answer = ''.join(full_answer)
                    db_conversation = Conversation(
                        question=request.question,
                        answer=complete_answer
                    )
                    db.add(db_conversation)
                    db.commit()
                    
                except Exception as e:
                    yield f"\n[Error: {str(e)}]"
            
            response = StreamingResponse(
                generate(),
                media_type="text/plain; charset=utf-8"
            )
            
            return response
        else:
            answer = await deepseek_server.query(request.question, stream=False)
            
            db_conversation = Conversation(
                question=request.question,
                answer=answer
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
            return DeepSeekResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
