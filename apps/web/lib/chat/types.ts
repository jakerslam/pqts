export type TurnRole = "user" | "assistant";
export type TurnStatus = "pending" | "sent" | "error";

export interface ChatTurn {
  id: string;
  role: TurnRole;
  text: string;
  status: TurnStatus;
  createdAt: string;
  errorMessage?: string;
}

export interface AssistantTurnResponse {
  assistant_message: string;
}
