import React, { FunctionComponent, useState } from 'react';
import { Container, FormControl } from 'react-bootstrap';

interface Props {
    onSubmit: (slackName: string) => void,
    newUser: boolean
}

const Authenticate: FunctionComponent<Props> = ({ onSubmit, newUser }) => {
    const [username, setUsername] = useState<string>('');
    const greeting = newUser 
                     ? "Hi, I don't think we've met! 👋" 
                     : "So, you're an imposter, huh? 👀";

    return (
        <Container className="mt-2 mb-2">
            <h1>{greeting}</h1>
            <p className="lead">Could you tell me what your Slack username is?</p>

            <p>
                This is the handle that people can use to refer to you after the
                @ sign. For example, I'm <code>@Parth</code>. Head over to Slack
                and type '@' into a message box, then type your name. Hit Enter
                and then paste the content of the message box here.
            </p>

            <FormControl
                value={username}
                placeholder="@Parth"
                onChange={(e) => setUsername(e.target.value)}
            />
        </Container>
    );
}

export default Authenticate;