import Link from '@docusaurus/Link';

import {
  SectionDescription,
  SectionTitle,
  SectionWrapper,
} from '@site/src/components/ui/SectionWrapper';
import OpenCollectiveSponsors from './OpenCollectiveSponsors';
import OpenCollectiveBackers from './OpenCollectiveBackers';
import OpenCollectiveButton from './OpenCollectiveButton';
import styles from './styles.module.scss';

import { useOpenCollective } from './use-open-collective';

export default function SponsorsAndBackers() {
  const { goldSponsors, silverSponsors, bronzeSponsors } = useOpenCollective();

  return (
    <SectionWrapper className={styles.section}>
      <SectionTitle>スポンサーと後援者</SectionTitle>

      <SectionDescription>
        <p>
          JHipsterが仕事に役立つとお考えの方は、ぜひ貴社に          
          <Link href="https://opencollective.com/generator-jhipster#sponsor">
            スポンサー
          </Link>
          となっていただきオープンソースのプロジェクトをサポートするようご検討をお願いします。
          また 
          <Link href="https://opencollective.com/generator-jhipster#backer">
            後援者
          </Link>
          となり、個人的なプロジェクトの支援も可能です。
        </p>
      </SectionDescription>

      <OpenCollectiveButton />

      {/* Gold sponsors */}
      <OpenCollectiveSponsors
        title="Thank you to our gold sponsors!"
        sponsors={goldSponsors}
        imageSize={140}
      />

      {/* Silver sponsors */}
      <OpenCollectiveSponsors
        title="シルバースポンサーとなっていただき、感謝いたします！"
        sponsors={silverSponsors}
      />

      {/* Bronze sponsors */}
      <OpenCollectiveSponsors
        title="ブロンズスポンサーとなっていただき、感謝いたします！"
        sponsors={bronzeSponsors}
      />

      <OpenCollectiveButton />

      {/* Backers */}
      <OpenCollectiveBackers />
    </SectionWrapper>
  );
}
