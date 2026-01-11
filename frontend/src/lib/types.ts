/**
 * Types for the AI Chat Platform frontend.
 */

/**
 * Event types received from the backend SSE stream.
 */
export interface StreamEvent {
  type:
    | "text"
    | "tool_start"
    | "tool_result"
    | "user_input_required"
    | "done"
    | "error";
  text?: string;
  tool_id?: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  content?: string;
  is_error?: boolean;
  session_id?: string;
  result?: string;
  tool_result?: string;
  error?: string;
  cost?: number;
  questions?: UserQuestion[];
}

/**
 * Question for user input prompts.
 */
export interface UserQuestion {
  question: string;
  header: string;
  options: Array<{ label: string; description: string }>;
  multiSelect: boolean;
}

/**
 * User prompt data from the agent.
 */
export interface UserPrompt {
  questions: UserQuestion[];
}
