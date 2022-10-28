# Contributing Guidelines
Thank you for your interest in contributing to the graph-notebook project! Whether it's a bug report, new feature, new notebook, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Before reporting a bug/feature request, or creating a pull request, please ensure that:

1. You have checked there aren't already open or recently closed issues/pull requests for your request.
2. You are working against the latest source on the `main` branch.
3. You open an issue to discuss any significant work - we would hate for your time to be wasted.

## Security Issue Notifications
If you discover a potential security issue in this project, we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please **do not** create a public Github issue.

## Reporting Bugs/Feature Requests
We welcome you to use the GitHub issue tracker to report bugs or suggest features. Please try to include as much information as you can. Details like the following are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment

## Contributing code via Pull Requests
Contributions via pull requests are much appreciated. 

To send us a pull request, please:

1. Fork the repository.
2. Modify the source; please focus on the specific change you are contributing. If you also reformat all the code, it will be hard for us to focus on your change.
3. Ensure local tests pass.
4. Commit to your fork using clear commit messages.
5. Send us a pull request, answering any default questions in the pull request interface.
6. In your local branch, modify the “Upcoming” section in the ChangeLog.md file with a new entry that includes a brief description of your changes, as well as a link to the open pull request (see sample format below). Push the ChangeLog update to the pull request branch.

    `- Added a change. ([Link to PR](https://github.com/aws/graph-notebook/pull/1))`

7. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

## Contributing sample notebooks via Pull Requests
We welcome any new contributions on how to use the graph-notebook to solve real-world graph problems! Before sending us a pull request, please open an issue to discuss your notebook idea. Here are some additional guidelines to expedite the review process:

1. **Use of sample data and images:** You will be asked to verify the licensing of your data and images. ** For data, provide a way for the notebook to be able to programmatically download the data within a cell. For images, provide a hosted link (e.g., Amazon S3, CloudFront). We try to keep the package size of graph-notebook small so no data or images should be part of the pull request.

2. **Standalone tutorials:** Our sample notebooks typically automate as much as possible using sample configurations and commands within Cells. The idea is that a user can run through a sample notebook with minimal required inputs and configuration outside of the notebook. *For Amazon Neptune tutorials: provide a way or advise the user to create a new Neptune cluster for the tutorial with desired configurations as applicable.*

3. **Naming/numbering of notebooks:** Our notebooks typically follow some themes, such as by language, by business application, or by feature. Before merging, check with a graph-notebook admin to come up with an agreed folder-path and naming.

4. **Running cells:** Provide a brief explanation for each cell on the purpose of running the cell and expected result. For example, after running a `%seed` command on a sample dataset, add a follow-up cell with a graph query to show how many nodes/edges were added and write the expected numbers to compare to.

5. **Cleaning up:** Provide a way (and be extra careful) to **ONLY** delete the data and resources created as part of tutorial, once the tutorial concludes.

6. **Testing:** During testing, each cell should output expected results successfully using the provided configurations, to be validated by a reviewer.

7. **Structure:** For longer sample notebooks, include a Table of Contents to help users quickly navigate. Create a Conclusion section and provide calls-to-action that users can follow-up on the specific topics if they want to learn more.

## Finding contributions to work on
Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/duplicate/help wanted/invalid/question/wontfix), looking at any 'help wanted' issues is a great place to start.

## Code of Conduct
This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with any additional questions or comments.

## Licensing

See the [LICENSE](LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.

We may ask you to sign a [Contributor License Agreement (CLA)](http://en.wikipedia.org/wiki/Contributor_License_Agreement) for larger changes.
