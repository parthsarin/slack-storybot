import React, { FunctionComponent, KeyboardEvent, useState } from 'react';
import { Button, Container, FormControl } from 'react-bootstrap';

interface Props {
    onSubmit: (slackName: string) => void,
    newUser: boolean
}

const cleanName = (username: string): string => {
    // Strips the @ signs from the beginning of the string and trailing
    // whitespace.
    let output: string = username.trim();           // whitespace
    output = output.replace(new RegExp("^@+"), ""); // @ signs at the front
    
    return output
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
                and type '@' into a message box, then search for yourself. 
                Select the correct profile by clicking on it or pressing Enter
                and then paste the content of the message box here.
            </p>

            <FormControl
                value={username}
                placeholder="@Parth"
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e: KeyboardEvent<HTMLInputElement>) => {
                    if (e.code === 'Enter') {
                        onSubmit(cleanName(username));
                    }
                }}
            />

            <Button
                variant='primary'
                className="mt-2 float-right"
                onClick={() => onSubmit(cleanName(username))}
            >
                Submit
            </Button>
        </Container>
    );
}

export default Authenticate;