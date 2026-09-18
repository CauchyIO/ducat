# Assess and optimize your Databricks setup with this Claude skill 
*Databricks Usage and Costs Assessment Tool (DUCAT) reviews your current platform and suggests improvements to make it cost less*

Brace yourselves: it is that day of the month again. Your cloud bill has just arrived and, with it, a myriad of questions no one is able to properly answer: 

* Why is our bill higher this month? 
* What team or project is driving up the costs? 
* How can we possibly cut the bill while delivering on our service level agreements? 
* Who of you decided it was a good idea to leave a virtual machine (VM) active over the weekend and generate the cloud cost equivalent to leaving the lights on in your house while you go abroad on a month vacation? No judgment (okay, maybe some judgment). 

Most likely, you have had to ask or answer at least one of these questions. The good news is you are not alone! According to a survey conducted in 2025 with about 2,300 participants across the entire globe, [94% of IT leaders are struggling to understand and optimize cloud costs](https://news.cision.com/softwareone/r/94--of-it-leaders-struggle-to-optimize-cloud-costs,c4231173). 

Like many others, we at Cauchy have felt these challenges first-hand, and we have [written before](https://blog.cauchy.io/p/the-complete-guide-to-databricks) about how we practice FinOps, the discipline of managing cloud spend jointly between engineering and finance. On Databricks in particular, a handful of [system tables](https://docs.databricks.com/aws/en/admin/system-tables/) hold most of the answers. They let you identify the major cost drivers and review the platform critically, looking for optimizations such as tightening an auto-termination schedule or choosing a cheaper VM for your extract, transform, and load (ETL) jobs. 

## Where LLMs come in 
As individual data practitioners at Cauchy, we know what sources to explore and what considerations to bear in mind in order to diagnose Databricks overspending and come up with cheaper alternatives. However, this is not as simple as it seems, even for experienced Databricks users and especially for teams that do not have Databricks specialists on hand. Thus, we set out to create a skill that is able to distill Databricks cost optimization knowledge into a generalizable approach that can be used by both experienced engineers and newcomers to the platform alike. 

One of the primary goals when creating the skill was that it adhere to the following standards when given a request to optimize a Databricks scope: 

* Consistently follow the same user workflow procedure. 
* Review and optimize Databricks scope settings consistently against predefined criteria. 
* Consistently provide a standardized, structured report covering every relevant aspect of the workflow. 

The three standards should hold across different user runs, turning the skill workflow into a semi-deterministic cost assessment where the user is prompted to define the constraints of the optimization problem, and the task of reading system tables and extracting conclusions from them is delegated to your choice of Claude model. 

In this blog post, I will write about the approach we used to define the skill, followed by the workflow it runs to first review, then optimize, a Databricks setup. I will also cover some of its limitations: some we have tackled, others remain open. 

So let's get on with it!

## How it works 

### Two governing rules 
* Scope confirmations precedes analysis: Global optimization is never a valid starting point. Prior to the assessment, the user must provide key information about the optimization scope in terms of resources, attribution method, period of analysis, etc. Only after this is done can the optimization be meaningful.
* Read-only workflow: no create, update, start, stop, resize, or delete operations are ever invoked. 

### The workflow at a glance 

DUCAT never runs end to end on its own. It stops four times to ask you something, and it cannot continue until you answer. We call those stops gates, and the diagram below shows only them. Everything between two gates is DUCAT reading system tables and coming back with a result for you to judge.

```mermaid
flowchart LR
  START(["'Can you optimize my Databricks project?'"]) --> G1{{"Gate 1: You choose the authentication and access route"}}
  G1 --> G2{{"Gate 2: You choose and confirm the scope"}}
  G2 --> G3{{"Gate 3: You confirm the baseline matches what you know"}}
  G3 -->|"no, something is off"| G2
  G3 -->|"yes"| G4{{"Gate 4: You choose which cost-saving cards go forward"}}
  G4 --> STOP(["DUCAT hands off the design.<br/>Nothing in your workspace has changed"])

  classDef gate fill:#DDEEEB,stroke:#0F766E,stroke-width:1.5px,color:#0B3D39;
  classDef term fill:#12212B,stroke:#12212B,color:#F1F4F6;
  class G1,G2,G3,G4 gate;
  class START,STOP term;
```
### The user gates
#### 1. Choosing an authentication and access route 
Before DUCAT reads a single row, you choose how it reaches your workspace. We have defined two separate routes, each of which uses a different authentication token and access gate:

- **Read-only service principal + Databricks MCP Server** (recommended default setting): a [step-by-step](../docs/getting-started.md) tutorial is provided on how to provision a read-only service principal, and how to mint a token linked to that identity that is used to reach the Databricks MCP server. Since the service principal created is read-only, this approach ensures that the workspace will not be modified by the skill (a constraint enforced numerous times in Markdown text that we have observed can be violated if the user pressures Claude hard enough).

- **Databricks personal account + Databricks CLI**: in order to follow this route, all that is needed from you is to have logged in to your Databricks workspace with your personal account via the CLI. It is important to bear in mind that, if you choose to use the skill with this route, you might allow Claude to modify the provisions of your workspace or make writes to your database. However, even if you choose this method, to provide an extra layer of security, we have designed the skill so that Databricks bash commands are only ever executed after explicit authorization from the user. This is set in [.claude/settings.json](../.claude/settings.json), where Bash(databricks:*) has the ask permission.

Note that we have created these two predefined access and authenticaiton routes, but you can tinker with the setup and create your own. For example, you might want to interact with your workspace via the MCP server using your personal account. However, this will require you to go actively change the provided workflow or expand it so that it is able to account for your custom route.

#### 2. Choosing a scope 
This is where "optimize my Databricks" gets turned into a question DUCAT can actually answer. 

If your request already names a [scope](../references/opportunity-catalog.md), DUCAT restates it and asks you to confirm. If something is missing that could change the assessment, DUCAT asks for it. For example:

- What kind of thing are we looking at? A job, a pipeline, a SQL warehouse, a serving endpoint, or a whole team's spend?
- What are those objects called in the workspace?
- What time period should be used for the analysis?

Answering these questions helps narrow down the scope of optimization. If you cannot determine the scope (what elements of the project/workspace you want to optimize), DUCAT offers a bounded, coarse scan of your major cost drivers. After user consent is granted, the scan returns candidate scopes and, once you pick one, you arrive back at this gate. A confirmed scope is a hard requirement for a targeted read.

Based on the information provided by the user and the remaining available evidence, our skill discriminates between the following types of attribution, ordered in decreasing order in terms of degree of confidence:

* **Native.** The billing record itself names the object, through a job ID, a warehouse ID, a pipeline ID, or similar. The platform did the work, and DUCAT looks for this first. 
* **Manual.** A person asserted that the object belongs to the scope, either by confirming it in the conversation or by tagging it in the workspace. 
* **Inferred.** The object was matched by name or convention, with nothing on the record to confirm it. 
* **Unallocated.** Spend in the period that matched nothing. It gets its own line and is never spread across the others. 

The four stay separate all the way to the final report because collapsing them into one total destroys your ability to judge it. A figure that is 80% native and 20% inferred is a different figure from one that is 20% native and 80% inferred, even when they add up to the same amount. 

Figures are always reported along with their attribution type, rather than simply provided. A job that runs on shared all-purpose compute leaves no job ID on the billing record, so per-job attribution is structurally impossible there. A cluster launched from a pool inherits the pool's tags, so the cluster's own tags never reach the cloud bill. A warehouse serving several teams has to be split in proportion to each team's query time, and the queries that carried no team tag are unallocated spend, not free spend. 

#### 3. Confirming a baseline 
After the scope has been confirmed, a series of targeted reads are done against the system tables of your Databricks workspace. The next step in the workflow is consolidating the information coming from the output of those queries and replaying it to the user. Two possible scenarios follow:

- Scenario 1: user acknowledges the baseline suggested by the skill and gives a clear *go ahead*, thus proceeding to the next step.
- Scenario 2: user disputes one or more aspects of the suggested baseline. What follows then is a new, refined baseline that incorporates the feedback of the user, bringing them to the beginning of this step again.

#### 4. Selecting one or several cost optimization paths 
Only now that the baseline has been confirmed by the user does the skill look for potential cost saving recommendations. In order to create such recommendations, the skill makes use of two manually curated sets of references:

- Data sources: a list of all the available sources of evidence the skill might use for the recommendation, specifying order of preference, help on interpreting query results, rules on making conclusions, among others. It serves as sort of an alongside manual for the skill to follow along with querying the Databricks workspace, or having to resort to any of the alternative sources.

- Opportunity catalog: a number of files pinpointing different ways in which specific scopes can be made cheaper. Think of it as the tools in your belt as a cloud cost saving specialist. For example, the following actions can be potentially performed in order to optimize a Databricks job: for example, right-sizing the job cluster, or modifying the autotermination settings. 

What comes out as a result of this process is a shortlist of cost saving opportunities. Each opportunity will contain a concise description of the suggested change and the entailed savings, among other details.

You choose which cards go forward into the final report and which ones are discarded.

### Generating report 
The engagement ends with one Markdown document, `cost-optimization-design.md`, with the following sections:

1. Decision summary: a simplified overview of the whole cost optimization process, from initial selection of project scope and period for assessment, to chosen opportunities and estimated savings.
2. Scope and evidence: the Databricks objects included in the asessment and evidence sources used for the cost claims.
3. Current-state baseline: current cost components, utilization measures and operational drivers of the chosen scope.
4. Opportunity disposition: every opportunity that was suggested to you as a potential cost optimization, whether it was accepted or rejected.
5. Target-state design: design of your project in its final state inlcuding the cost saving opportunities that you accepted.
6. Financial case: estimation of "before and after" platform costs, including attribution type of cost (as described below) and modeled values for potential re-implementation.
7. Implementation and verification: measures to verify the implementation of the target-state design has been successful.
8. Open decisions and limitations: missing evidence, unresolved ownership and insufficiently supported claims that arose during the assesment.

## An example run 
Enough theory. To show what the workflow looks like in practice, I will walk you through a real run. Steven, a colleague at Cauchy, pointed DUCAT at his [RDW project](https://blog.cauchy.io/p/the-secrets-of-bronze-silver-and): a medallion-style ETL (a download job, then bronze/silver/gold processing) deployed as a Databricks Asset Bundle, with its own job compute and its own SQL warehouse packaged in the bundle. It was a cold run: Steven had never used the skill before and nobody was coaching him. His opening message was as vague as they come:

> RDW is costing more than expected, can you investigate?

Let's follow it gate by gate.

### Gate 1. Authentication and access route 
Steven's setup already pointed at the Databricks MCP server, so the first gate was settled before he typed anything: the authentication method would be a read-only service principal, and the access route the Databricks MCP Server.

### Gate 2. Choosing a scope 
"RDW" names something, but not something DUCAT can query. Before touching a system table it asked three questions in one go: 
- What kind of scope is RDW? 
> A DAB project.
- How is the project spend identified? 
> Via the named resources (job compute & warehouse) packed in the project DAB.
- What period should the skill analyze? 
> Last 30 days against the prior 30.

Those answers told DUCAT where to look. It searched `system.lakeflow.jobs`, `system.compute.warehouses` and `system.lakeflow.pipelines` for RDW-named objects and came back with three live jobs and one serverless warehouse. Every one of them carries its own ID on the billing record, so the attribution was **native** throughout and the unallocated line stayed empty.

### Gate 3. Confirming a baseline 
The period comparison came back with a number that explained the surprise: $0.02 in the prior 30 days, $62.01 in the last 30. Of that, $59.95 was the bundle's serverless warehouse and $2.06 was serverless job compute. 

That was replayed to Steven as one question: does this baseline match your understanding, with the option to dispute the numbers or DUCAT's understanding of the scope. 
> Confirmed, continue
He confirmed, and only then did the skill go looking for savings.

### Gate 4. Selecting one or several cost optimization paths 
With a confirmed scope of "jobs plus warehouse", DUCAT read the opportunity catalog, then checked a relevant piece of online documentation to verify one fact it was about to rely on: the serverless warehouse auto-stop floor is 5 minutes in the UI but 1 minute through the API, which is how bundles deploy. It then presented three cards:

- **Card A (recommended):** cut the warehouse auto-stop from 10 to 1 minute in the bundle. Modeled saving of $42–52 a month for a one-line change; the trade-off is a few seconds of cold resume on the first query of each burst.
- **Card B:** delete the dedicated warehouse and route RDW's dev queries to the workspace's shared starter warehouse. Up to the full $59.95 at scope level, but a smaller and less certain account-level saving, and RDW's SQL spend stops being separately attributable.
- **Card C:** a cost anomaly alert, explicitly labeled as not a saving; it would have flagged this increase on about 5 August instead of at month end.

> B: drop warehouse, use shared
Steven picked Card B, not the recommended one. This is the gate working as intended: DUCAT quantifies and recommends, but which trade-off to accept is a decision only the person who owns the project can make.

### Generating report 
Twelve minutes after a one-line question, the engagement ended with [`cost-optimization-design.md`](link/to/markdown) written to the repository, and with no change made to the workspace. Click on the file link to read the whole assessment report.

## The safeguards 
The skill ships with packaged knowledge: a table of reference prices, SKU and product names, the routing from scope to opportunity file, and the mechanisms behind each optimization. All of that is distilled from online documentation material the vendor publishes and updates. This entails a risk that out-of-date information can be used as a base to generate a platform assessment, which a user can hardly tell by reading the assessment if at all. For example, in the months we have been working on this, DLT was renamed to Lakeflow Spark Declarative Pipelines, Genie moved to pay-as-you-go under a SKU that carries no list price at all, and the Standard tier was scheduled for retirement. None of those changes announces itself inside a reference file.

We handle this in three layers.

**Every vendor fact carries a date, and loses to a live query.** Each reference states when it was distilled and by when it must be reviewed, and the price table records the last time it was re-verified against `system.billing.list_prices`. Live system tables and current official documentation outrank static documentation every time, and when the skill corrects one it says so in the assessment. 

**A commit hook refuses stale references.** [`check-consistency.py`](../tools/check-consistency.py) runs before every commit and again in CI. It fails on a review date that has expired, a price baseline older than 90 days, a scope file the routing table does not name (or a route to a file that does not exist), and a relative link that no longer resolves. 

**A weekly job watches the sources themselves.** A distillation date says when someone last read a source, not whether the source has changed since. [`check-upstream.py`](../tools/check-upstream.py) pins the change signal each upstream page publishes and compares it against the live one every Monday, raising an issue when a source has moved so that a human owes a re-read. It runs on its own clock rather than as a commit hook, because committing must never depend on Microsoft being reachable.

## Evaluation report
Although the results we had obtained using the skill in our own workspace seemed very promising, a manual testing approach is not sufficient evidence to ensure the two following assertions:

- The skill performs as expected in a variety of possible scenarios, respecting the given guardrails and pre-defined workflow. Each of this testing scenarios is commonly known in the space as an evaluation.
- The skill brings an added value compared to using vanilla Claude for the task of Databricks platform cost optimization, visibly observed when comparing the results of the evaluations of Claude using the skill against the results of the evaluations of vanilla Claude.

As stated in the section [Limitations and aspects to consider](#limitations-and-aspects-to-consider), one feature the skill lacks as of today is a dedicated evaluation suite. However, we did run a dynamically created evaluation suite using [skill-creator's run-eval script](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/scripts/run_eval.py). We provide a link to the full evaluation report on the appendix if you are interested in reading it in full. In summary, the skill was tested across the following axis:

1. Scope confirmation must precede workspace reads: user explicit choice of optimization scope effectively unblocks reading system tables and making API requests.
2. Remain read-only in all circumstances: do not ever try to implement one of the suggested cost saving opportunities, even when under user pressure.
3. Attribution is kept honest: Native, manual, inferred and unallocated cost stay separate throughout the assessment and it is always explicitly stated.
4. Claims are bounded by evidence: no cost claim is ever made without the source of evidence accompanying the figure.
5. Agent stays on-rails within the pre-defined workflow during the session: skill does not take unexpected turns in following the steps sequentially.

A total of ten tests were conducted on DUCAT (formerly known internally as databricks-cost-optimizer): five different prompts with and without the skill enabled. The results are summarized in the table below:
![image](benchmark-results.png)

- Using DUCAT lifted the pass rate by 52% compared with vanilla Claude. Vanilla Claude results also variated highly across different queries (std dev. of 32 points)

- Tests with the skill enabled took 149.6 seconds longer than vanilla Claude on average (approximately 2.5 minutes). Most likely a consequence of the highly structured workflow the session follows when the skill is enabled compared to when it is not.

- Finally, token consumption was also higher when the skill was enabled by 9038 tokens on average. The most likely reason is the fact that several reference files have to be loaded for the skill to be invoked.

In conclusion: the skill buys a large correctness gain (+52 points) for a moderate cost (+40% time, +9% tokens). Based on the result, the aspects where the skill seems to overperform vanilla Claude are the following:

## Limitations and aspects to consider 
**Read-only is not strictly enforced by the skill.** Despite the many times it is mentioned in the skill that being read-only is one of the governing principles, we have observed in one session that the skill has executed its design whenever it has had the necessary grants to do so after being prompted by the user. Read-only can be enforced by using an identity with read-only grant, which is why we provide step-by-step instructions to create a read-only service principal that cannot possibly modify your workspace.

**There is no dedicated eval suite yet.** Testing has been manual: colleagues run the skill cold, and we read the transcript and the report. Furthermore, we have rUn a dynamically generated eval suite generated by Anthropic's skill-creator plugin. Apart from these facts, there is not a dedicated eval suite running on a specific schedule or triggered by spefic events. Ahead of us lays the need to design and implement these tests to ensure the tool behaves according to the expectation on a number of scenarios and grade it accordingly.

**Azure Databricks and Claude Code only.** AWS, GCP and other agent harnesses are untested.

**The numbers are list price, not what you pay.** System tables know how many DBUs you used, not what you were charged for them. DUCAT multiplies usage by the published price, which is the figure Databricks puts on its pricing page, not the one on your invoice. Your invoice will be lower if you have a negotiated discount, and higher if your scope runs on classic compute, because the virtual machines behind it are billed by Azure and never show up in a Databricks table. Only Azure Cost Management knows the real number, and when DUCAT can reach it, the billed and list figures are reported side by side, never merged. When it cannot, every figure in the report says so. And even with your discounted rate in hand, there is one thing DUCAT cannot tell you: whether that discount still applies once you change the setup it recommends.

## Conclusions 

## Appendix 

### Full workflow diagram 

```mermaid
flowchart TD
  START(["'Can you optimize my Databricks project?'"]) --> ROUTE{{"Gate 1: Choosing authentication route"}}
  ROUTE -->|"service principal: the platform enforces read-only"| Q{"Did you name<br/>the scope<br/>in the original request?"}
  ROUTE -->|"your own account: only your consent bounds it"| BRIEF["DUCAT briefs you on the risk<br/>and waits for a clear yes"]
  BRIEF --> Q

  Q -->|"no"| OFFER["DUCAT offers a quick scan<br/>of what is driving spend"]
  OFFER -->|"you say go"| SCAN["A bounded, read-only look<br/>at spend by product"]
  SCAN --> CAND[/"Show a list of candidate scopes.<br/>Not findings yet"/]
  CAND --> GATE

  Q -->|"yes"| GATE{{"Gate 2: You choose and confirm the scope.<br/>Nothing specific is read before this"}}
  GATE -->|"you unlock targeted reads"| PRE["DUCAT checks which evidence<br/>sources it can actually reach"]
  PRE --> CLAIM[/"Constraint: What cannot be reached cannot be claimed"/]
  CLAIM --> ATTR{{"Gate 3: You agree what counts as this scope's cost<br/>and what is left out"}}
  ATTR --> BASE["DUCAT measures what the scope<br/>costs today, from billing data"]
  BASE --> REPLAY{{"Gate 4: DUCAT plays the baseline back to you.<br/>Does it match what you know?"}}
  REPLAY -->|"no, something is off"| ATTR
  REPLAY -->|"yes"| SHORT["DUCAT lists ways to spend less.<br/>Each is a decision card with evidence and trade-offs"]
  SHORT -->|"the numbers moved"| REPLAY
  SHORT --> SEL{{"Gate 5: You choose which cards go forward"}}
  SEL -->|"you unlock a recommendation"| PORT["DUCAT prices the chosen changes together,<br/>allowing for how they interact"]
  PORT --> HAND["DUCAT writes the design handoff:<br/>steps, risks, and how to verify the saving"]
  HAND --> STOP(["DUCAT stops here.<br/>Nothing in your workspace has changed"])

  subgraph KEY["Key"]
    direction LR
    K1{{"&nbsp;&nbsp;"}} ~~~ T1["DUCAT stops and waits for your answer"]
    K2["&nbsp;&nbsp;"] ~~~ T2["DUCAT does this itself, read-only"]
    K3{"&nbsp;"} ~~~ T3["Answered from your request, no question asked"]
    K4[/"&nbsp;&nbsp;"/] ~~~ T4["A rule that limits the next step, not an action"]
    K5(["&nbsp;&nbsp;"]) ~~~ T5["Where the flow starts or ends"]
  end

  classDef gate fill:#DDEEEB,stroke:#0F766E,stroke-width:1.5px,color:#0B3D39;
  classDef term fill:#12212B,stroke:#12212B,color:#F1F4F6;
  classDef note fill:#F1F4F6,stroke:#8FA3B0,stroke-dasharray:4 3,color:#3D4E5A;
  class ROUTE,GATE,ATTR,REPLAY,SEL,K1 gate;
  class START,STOP,K5 term;
  class CAND,CLAIM,K4 note;
  classDef plain fill:none,stroke:none,color:#0B3D39,font-size:11px;
  class T1,T2,T3,T4,T5 plain;
  style KEY fill:#DDEEEB,fill-opacity:0.5,stroke:#0F766E,stroke-dasharray:2 4,color:#0B3D39;
```
