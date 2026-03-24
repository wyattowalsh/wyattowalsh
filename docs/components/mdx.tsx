import defaultMdxComponents from 'fumadocs-ui/mdx';
import { ImageZoom } from 'fumadocs-ui/components/image-zoom';
import { Tab, Tabs } from 'fumadocs-ui/components/tabs';
import { Accordion, Accordions } from 'fumadocs-ui/components/accordion';
import { Step, Steps } from 'fumadocs-ui/components/steps';
import { File, Folder, Files } from 'fumadocs-ui/components/files';
import { InlineTOC } from 'fumadocs-ui/components/inline-toc';
import type { MDXComponents } from 'mdx/types';

export function getMDXComponents(components?: MDXComponents): MDXComponents {
  return {
    ...defaultMdxComponents,
    img: (props) => <ImageZoom {...(props as any)} />,
    Tab,
    Tabs,
    Accordion,
    Accordions,
    Step,
    Steps,
    File,
    Folder,
    Files,
    InlineTOC,
    ...components,
  };
}

export const useMDXComponents = getMDXComponents;
