/**
 * Types for the AI Chat Platform frontend.
 *
 * Note: Most types are now provided by @ai-sdk/react.
 * This file contains custom types specific to this application.
 */

/**
 * Question for user input prompts (AskUserQuestion tool).
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
