import PropTypes from "prop-types";
import React from "react";
import { Link } from "react-router-dom";
import { Button, Header, Item } from "semantic-ui-react";

import DocumentTitle from "../../../DocumentTitle";

const ProjectAdminPage = ({ project }) => (
  <React.Fragment>
    <DocumentTitle title={project.name} />
    <Header as="h1" dividing>
      {project.name}
    </Header>
    <div>
      <Link to="/projects/">Return to all projects</Link>
    </div>
    <Header as="h2">Manage</Header>
    <p>
      <Link to={`/project/${project.id}/variants`}>Upload variants</Link>
    </p>
    <Header as="h2">Curators</Header>
    <Item.Group>
      {Object.entries(project.assignments).map(([curator, { total, completed }]) => (
        <Item key={curator}>
          <Item.Content>
            <Item.Header>{curator}</Item.Header>
            <Item.Meta>
              {completed} / {total} variants curated
            </Item.Meta>
          </Item.Content>
        </Item>
      ))}
    </Item.Group>
    <Header as="h2">Results</Header>
    <p>
      {project.variants.curated} / {project.variants.total} variants curated
    </p>
    <Button as="a" download href={`/api/project/${project.id}/results/`}>
      Download
    </Button>
  </React.Fragment>
);

ProjectAdminPage.propTypes = {
  project: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    assignments: PropTypes.objectOf(
      PropTypes.shape({
        total: PropTypes.number.isRequired,
        completed: PropTypes.number.isRequired,
      })
    ).isRequired,
    variants: PropTypes.shape({
      total: PropTypes.number.isRequired,
      curated: PropTypes.number.isRequired,
    }).isRequired,
  }).isRequired,
};

export default ProjectAdminPage;
