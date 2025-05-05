var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

// Navigate to the Project page for the selected Protocol
dagcomponentfuncs.ProtocolLink = function (props) {
    return React.createElement(
        'a',
        {
            href: './project/' + props.value, // Updated to navigate to the Project page
            target: '_self',
            onClick: function () {
                // Clear selection after click
                if (props.api) {
                    props.api.deselectAll();
                }
            },
        },
        props.value
    );
};
// Navigate to the Analysis Task page for the selected Project
dagcomponentfuncs.ProjectLink = function (props) {
    return React.createElement(
        'a',
        {
            href: './analysis-task/' + props.value, // Navigate to the Analysis Task page
            target: '_self',
            onClick: function () {
                // Clear selection after click
                if (props.api) {
                    props.api.deselectAll();
                }
            },
        },
        props.value
    );
};
// Navigate to the Analysis Version page for the selected Task
dagcomponentfuncs.TaskLink = function (props) {
    return React.createElement(
        'a',
        {
            href: './analysis-version/' + props.value,
            target: '_self',
            onClick: function () {
                // Clear selection after click
                if (props.api) {
                    props.api.deselectAll();
                }
            },
        },
        props.value
    );
};

// Navigate to the Display Table page for the selected Version
dagcomponentfuncs.VersionLink = function (props) {
    return React.createElement(
        'a',
        {
            href: './display-table/' + props.context.selectedTask + '/' + props.value,
            target: '_self',
            onClick: function () {
                // Clear selection after click
                if (props.api) {
                    props.api.deselectAll();
                }
            },
        },
        props.value
    );
};
// Render the SDTM_Spec column as a clickable hyperlink
dagcomponentfuncs.LinkCellRenderer = function (props) {
    return React.createElement(
        'a',
        {
            href: props.value, // Use the value of the cell as the hyperlink URL
            target: '_blank', // Open the link in a new tab
            rel: 'noopener noreferrer', // Security best practice for external links
        },
        props.value // Display the URL as the link text
    );
};
dagcomponentfuncs.OpenFileRenderer = function (params) {
    if (params.value) {
        return `<a href="${params.value}" target="_blank">Open File</a>`;
    } else {
        return '';
    }
};