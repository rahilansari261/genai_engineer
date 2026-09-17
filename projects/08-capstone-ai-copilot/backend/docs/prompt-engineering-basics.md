# Prompt Engineering Basics

Prompt engineering is the practice of designing the input to a language model to reliably get the output you want, without changing the model itself. Because the same model can behave very differently depending on how a request is phrased, structured, or framed, small changes in a prompt often produce large changes in output quality — which is what makes prompt engineering worth treating as a real skill rather than an afterthought.

## System prompts versus user prompts

Most modern chat-based APIs separate a conversation into roles. The system prompt sets standing instructions for how the model should behave for the entire conversation — its persona, its constraints, the format it should reply in — and is typically not shown to the end user. The user prompt is the actual question or request for this turn. A well-written system prompt does more than describe a personality; it constrains behavior in specific, testable ways, such as refusing certain categories of request or always citing a source before making a claim.

## Few-shot prompting

Zero-shot prompting means asking a model to perform a task with no examples, relying entirely on its training. Few-shot prompting means including two or three worked examples of the task directly in the prompt before asking the model to perform it on new input. Few-shot examples are especially effective for getting a consistent output *format* — for instance, showing the model two examples of turning a sentence into a specific JSON shape reliably gets a third input converted into that same shape, far more reliably than describing the format in words alone.

## Chain-of-thought prompting

Chain-of-thought prompting asks a model to reason step by step before giving a final answer, rather than jumping straight to a conclusion. For tasks involving arithmetic, logic, or multi-step reasoning, simply adding an instruction like "think through this step by step" before the final answer measurably improves accuracy, because it gives the model room to work through intermediate steps as generated text, which the model itself then conditions on when producing the next step — rather than trying to reach the right answer in a single forward pass.

## Constraining and structuring output

Prompts can explicitly constrain the shape of a response: word or sentence limits, a required output format like JSON or a numbered list, a fixed set of allowed answers for a classification task, or an instruction to say "I don't know" rather than guess when the model is uncertain. This last instruction matters more than it sounds — by default, models are trained to always produce a plausible-sounding answer, so explicitly giving permission to decline is one of the more effective, and most commonly forgotten, techniques for reducing confidently wrong answers, a failure mode usually called hallucination.

## Iterating on prompts like code

A prompt that works well on the three examples you tested it with can still fail badly on the tenth. Treating prompt changes with the same discipline as code changes — keeping a fixed set of test cases, re-running them after every edit, and tracking whether a change actually improved results or just felt like it should — turns prompt engineering from guesswork into something closer to an engineering discipline, and is the same idea behind the adversarial testing suite used elsewhere in this repository's AI Safety Sandbox project.
